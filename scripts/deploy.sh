#!/bin/bash

# DecisionMakingArena Deployment Script
# Automates deployment to Databricks

set -e  # Exit on error

echo "========================================="
echo "DecisionMakingArena Deployment"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    echo "Checking prerequisites..."

    # Check if Databricks CLI is installed
    if ! command -v databricks &> /dev/null; then
        print_error "Databricks CLI not found. Install with: pip install databricks-cli"
        exit 1
    fi
    print_success "Databricks CLI found"

    # Check if authenticated
    if ! databricks workspace ls / &> /dev/null; then
        print_error "Not authenticated with Databricks. Run: databricks configure --token"
        exit 1
    fi
    print_success "Databricks authentication verified"

    # Check if .env file exists
    if [ ! -f .env ]; then
        print_error ".env file not found. Copy from .env.example and configure."
        exit 1
    fi
    print_success ".env file found"
}

# Create secrets scope
create_secrets() {
    echo ""
    echo "Setting up Databricks Secrets..."

    SCOPE_NAME="decision_making_secrets"

    # Check if scope exists
    if databricks secrets list-scopes | grep -q "$SCOPE_NAME"; then
        print_info "Secrets scope '$SCOPE_NAME' already exists"
    else:
        echo "Creating secrets scope..."
        databricks secrets create-scope --scope "$SCOPE_NAME"
        print_success "Secrets scope created"
    fi

    # Read .env file and create secrets
    echo "Creating secrets from .env file..."

    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ "$key" =~ ^#.*$ ]] && continue
        [[ -z "$key" ]] && continue

        # Remove quotes and whitespace
        value=$(echo "$value" | sed -e 's/^"//' -e 's/"$//' -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')

        # Skip if value is placeholder
        if [[ "$value" == *"your_"* ]] || [[ "$value" == *"<"*">"* ]]; then
            print_info "Skipping placeholder: $key"
            continue
        fi

        # Create secret
        echo "$value" | databricks secrets put-secret --scope "$SCOPE_NAME" --key "${key,,}" --binary-file /dev/stdin 2>/dev/null
        print_success "Secret created: $key"

    done < .env

    print_success "Secrets configured"
}

# Upload notebooks
upload_notebooks() {
    echo ""
    echo "Uploading notebooks to workspace..."

    WORKSPACE_PATH="/Shared/DecisionMakingArena"

    # Create directory
    databricks workspace mkdirs "$WORKSPACE_PATH"

    # Upload each notebook
    for notebook in notebooks/*.py notebooks/*.sql; do
        if [ -f "$notebook" ]; then
            filename=$(basename "$notebook")
            databricks workspace import "$notebook" "$WORKSPACE_PATH/$filename" --overwrite
            print_success "Uploaded: $filename"
        fi
    done

    print_success "Notebooks uploaded to $WORKSPACE_PATH"
}

# Run setup notebooks
run_setup_notebooks() {
    echo ""
    echo "Running setup notebooks..."

    WORKSPACE_PATH="/Shared/DecisionMakingArena"

    # Get cluster ID (use existing or create)
    read -p "Enter cluster ID (or press Enter to skip notebook execution): " CLUSTER_ID

    if [ -z "$CLUSTER_ID" ]; then
        print_info "Skipping notebook execution. Run notebooks manually in Databricks UI."
        return
    fi

    # Run data tables notebook
    echo "Running: 01_setup_data_tables.py"
    databricks jobs run-now --notebook-path "$WORKSPACE_PATH/01_setup_data_tables.py" --cluster-id "$CLUSTER_ID"
    print_success "Data tables setup completed"

    # Run vector search notebook
    echo "Running: 02_setup_vector_search.py"
    databricks jobs run-now --notebook-path "$WORKSPACE_PATH/02_setup_vector_search.py" --cluster-id "$CLUSTER_ID"
    print_success "Vector search setup completed"

    # Run UC functions notebook
    echo "Running: 03_deploy_uc_functions.sql"
    databricks jobs run-now --notebook-path "$WORKSPACE_PATH/03_deploy_uc_functions.sql" --cluster-id "$CLUSTER_ID"
    print_success "Unity Catalog functions deployed"
}

# Deploy Databricks App
deploy_app() {
    echo ""
    echo "Deploying Databricks App..."

    # Check if app.yaml exists
    if [ ! -f app.yaml ]; then
        print_error "app.yaml not found"
        exit 1
    fi

    # Deploy app
    databricks apps deploy app.yaml

    print_success "App deployment initiated"
    print_info "Check deployment status: databricks apps get decision-making-arena"
}

# Create Genie Spaces guide
show_genie_setup() {
    echo ""
    echo "========================================="
    echo "GENIE SPACES SETUP"
    echo "========================================="
    echo ""
    echo "You need to manually create 3 Genie Spaces in Databricks UI:"
    echo ""
    echo "1. Sales Genie"
    echo "   - Name: Production Sales Genie"
    echo "   - Tables: decision_making_prod.business_data.sales_data"
    echo ""
    echo "2. Finance Genie"
    echo "   - Name: Production Finance Genie"
    echo "   - Tables: decision_making_prod.business_data.financial_data"
    echo ""
    echo "3. Strategic Genie"
    echo "   - Name: Production Strategic Genie"
    echo "   - Tables: decision_making_prod.business_data.strategic_metrics"
    echo ""
    echo "After creating each space:"
    echo "   - Copy the Space ID from Settings"
    echo "   - Add to .env file"
    echo "   - Re-run: ./scripts/deploy.sh secrets"
    echo ""
}

# Main deployment flow
main() {
    case "${1:-all}" in
        prereq|prerequisites)
            check_prerequisites
            ;;
        secrets)
            check_prerequisites
            create_secrets
            ;;
        notebooks)
            check_prerequisites
            upload_notebooks
            ;;
        setup)
            check_prerequisites
            upload_notebooks
            run_setup_notebooks
            ;;
        app)
            check_prerequisites
            deploy_app
            ;;
        genie)
            show_genie_setup
            ;;
        all)
            check_prerequisites
            echo ""
            print_info "Full deployment will:"
            print_info "  1. Create secrets from .env"
            print_info "  2. Upload notebooks"
            print_info "  3. Deploy Databricks App"
            echo ""
            read -p "Continue? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                create_secrets
                upload_notebooks
                deploy_app
                echo ""
                print_success "Deployment complete!"
                echo ""
                show_genie_setup
                echo ""
                print_info "Next steps:"
                print_info "  1. Create Genie Spaces (see above)"
                print_info "  2. Run setup notebooks in Databricks UI"
                print_info "  3. Access your app at: https://your-workspace.cloud.databricks.com/apps/decision-making-arena"
            fi
            ;;
        *)
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  prereq      - Check prerequisites only"
            echo "  secrets     - Setup Databricks secrets"
            echo "  notebooks   - Upload notebooks to workspace"
            echo "  setup       - Run setup notebooks (requires cluster ID)"
            echo "  app         - Deploy Databricks App"
            echo "  genie       - Show Genie Spaces setup guide"
            echo "  all         - Full deployment (default)"
            echo ""
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
