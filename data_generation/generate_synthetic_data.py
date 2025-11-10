"""
Generate synthetic data for BioLabs Multi-Agent System

This script creates realistic business data for a company selling sugar substitutes:
- Sales transactions
- Inventory levels
- POS (Point of Sale) locations
- Marketing campaigns
- Customer segments
- Competitor intelligence
- Financial data
"""

import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import numpy as np
from faker import Faker

from config import (
    START_DATE, END_DATE, TOTAL_DAYS,
    PRODUCTS, CHANNELS, REGIONS,
    CUSTOMER_SEGMENTS, COMPETITORS, MARKETING_CHANNELS,
    NUM_TRANSACTIONS, NUM_POS, NUM_CAMPAIGNS
)

# Initialize Faker
fake = Faker(['es_MX', 'es_ES'])  # Spanish faker for Guatemala
random.seed(42)
np.random.seed(42)
Faker.seed(42)


class BioLabsDataGenerator:
    """Generate synthetic data for BioLabs"""

    def __init__(self):
        self.pos_list = []
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)

    def generate_pos_master(self) -> pd.DataFrame:
        """Generate POS (Point of Sale) master data"""
        print("Generating POS master data...")

        pos_data = []
        pos_id_counter = 1

        for channel_type, channel_info in CHANNELS.items():
            for _ in range(channel_info["count"]):
                pos_id = f"POS{pos_id_counter:04d}"

                # Generate realistic POS name based on channel
                if channel_type == "pharmacy":
                    pos_name = f"Farmacia {fake.last_name()}"
                elif channel_type == "specialty_grocery":
                    pos_name = f"Supermercado {fake.company()}"
                elif channel_type == "gym":
                    pos_name = f"Gimnasio {fake.first_name()}"
                else:  # hospital
                    pos_name = f"Hospital {fake.city()}"

                region = random.choice(REGIONS)
                city = fake.city()
                address = fake.address().replace('\n', ', ')
                active_since = START_DATE - timedelta(days=random.randint(30, 730))
                account_manager = fake.name()

                pos_data.append({
                    "pos_id": pos_id,
                    "pos_name": pos_name,
                    "pos_type": channel_type,
                    "region": region,
                    "city": city,
                    "address": address,
                    "active_since": active_since.date(),
                    "account_manager": account_manager,
                })

                self.pos_list.append({
                    "pos_id": pos_id,
                    "pos_name": pos_name,
                    "pos_type": channel_type,
                    "region": region,
                })

                pos_id_counter += 1

        df = pd.DataFrame(pos_data)
        df.to_csv(self.output_dir / "pos_master.csv", index=False)
        print(f"✓ Generated {len(df)} POS locations")
        return df

    def generate_sales_transactions(self) -> pd.DataFrame:
        """Generate sales transactions data"""
        print("Generating sales transactions...")

        transactions = []

        for _ in range(NUM_TRANSACTIONS):
            # Random date with some clustering (more recent = more transactions)
            days_ago = int(np.random.beta(2, 5) * TOTAL_DAYS)
            transaction_date = END_DATE - timedelta(days=days_ago)
            month = transaction_date.month

            # Random POS
            pos = random.choice(self.pos_list)

            # Random product based on channel affinity
            channel_type = pos["pos_type"]
            product_affinities = CHANNELS[channel_type]["product_affinity"]
            product_name = random.choices(
                list(product_affinities.keys()),
                weights=list(product_affinities.values())
            )[0]

            product_info = PRODUCTS[product_name]

            # Apply seasonality
            seasonality_factor = product_info["seasonality"][month]

            # Units sold (realistic distribution)
            base_volume = CHANNELS[channel_type]["avg_daily_volume_kg"]
            units_sold = max(0.5, np.random.gamma(2, base_volume / 2) * seasonality_factor)
            units_sold = round(units_sold, 2)

            # Calculate revenue and cost
            retail_price = product_info["retail_price_per_kg"]
            margin = CHANNELS[channel_type]["margin"]

            # BioLabs sells to channel at wholesale price
            wholesale_price = retail_price * (1 - margin)
            revenue = units_sold * wholesale_price
            cost = units_sold * product_info["cogs_per_kg"]

            transactions.append({
                "transaction_id": f"TXN{uuid.uuid4().hex[:12].upper()}",
                "date": transaction_date.date(),
                "product_name": product_name,
                "pos_id": pos["pos_id"],
                "pos_name": pos["pos_name"],
                "pos_type": channel_type,
                "units_sold": units_sold,
                "revenue": round(revenue, 2),
                "cost": round(cost, 2),
                "region": pos["region"],
            })

        df = pd.DataFrame(transactions)
        df = df.sort_values("date").reset_index(drop=True)
        df.to_csv(self.output_dir / "sales_transactions.csv", index=False)
        print(f"✓ Generated {len(df)} sales transactions")
        return df

    def generate_inventory_levels(self) -> pd.DataFrame:
        """Generate inventory levels snapshots"""
        print("Generating inventory levels...")

        inventory_data = []

        # Generate snapshots for last 90 days (daily)
        for days_ago in range(90):
            snapshot_date = END_DATE - timedelta(days=days_ago)

            for product_name in PRODUCTS.keys():
                # Simulate inventory with some randomness
                base_stock = random.uniform(800, 1500)
                current_stock = base_stock + np.random.normal(0, 200)
                current_stock = max(100, current_stock)

                reserved_stock = current_stock * random.uniform(0.1, 0.3)
                available_stock = current_stock - reserved_stock

                # Calculate daily sales average (last 30 days)
                daily_sales_30d_avg = random.uniform(10, 30)
                days_on_hand = int(available_stock / daily_sales_30d_avg)

                inventory_data.append({
                    "snapshot_date": snapshot_date.date(),
                    "product_name": product_name,
                    "location": "Main Warehouse",
                    "current_stock_kg": round(current_stock, 2),
                    "reserved_stock_kg": round(reserved_stock, 2),
                    "available_stock_kg": round(available_stock, 2),
                    "daily_sales_30d_avg": round(daily_sales_30d_avg, 2),
                    "days_on_hand": days_on_hand,
                })

        df = pd.DataFrame(inventory_data)
        df = df.sort_values(["snapshot_date", "product_name"]).reset_index(drop=True)
        df.to_csv(self.output_dir / "inventory_levels.csv", index=False)
        print(f"✓ Generated {len(df)} inventory snapshots")
        return df

    def generate_campaigns(self) -> pd.DataFrame:
        """Generate marketing campaigns data"""
        print("Generating marketing campaigns...")

        campaigns = []

        for i in range(NUM_CAMPAIGNS):
            product = random.choice(list(PRODUCTS.keys()))
            channel = random.choice(list(MARKETING_CHANNELS.keys()))
            segment = random.choice(list(CUSTOMER_SEGMENTS.keys()))

            # Campaign duration
            start_date = START_DATE + timedelta(days=random.randint(0, TOTAL_DAYS - 60))
            duration_days = random.randint(7, 90)
            end_date = start_date + timedelta(days=duration_days)

            # Budget and performance
            budget = random.uniform(5000, 50000)
            cac = MARKETING_CHANNELS[channel]["cac"] * random.uniform(0.8, 1.2)
            conversion_rate = MARKETING_CHANNELS[channel]["conversion_rate"]

            impressions = int(budget * random.uniform(15, 25))
            clicks = int(impressions * random.uniform(0.02, 0.08))
            conversions = int(clicks * conversion_rate * random.uniform(0.7, 1.3))

            # Revenue attributed
            avg_order = CUSTOMER_SEGMENTS[segment]["avg_order_value"]
            revenue_attributed = conversions * avg_order * random.uniform(0.8, 1.2)

            campaigns.append({
                "campaign_id": f"CMP{i+1:04d}",
                "campaign_name": f"{product} - {segment.title()} - {channel.title()}",
                "product": product,
                "channel": channel,
                "target_segment": segment,
                "start_date": start_date.date(),
                "end_date": end_date.date(),
                "budget": round(budget, 2),
                "impressions": impressions,
                "clicks": clicks,
                "conversions": conversions,
                "revenue_attributed": round(revenue_attributed, 2),
            })

        df = pd.DataFrame(campaigns)
        df = df.sort_values("start_date").reset_index(drop=True)
        df.to_csv(self.output_dir / "campaigns.csv", index=False)
        print(f"✓ Generated {len(df)} marketing campaigns")
        return df

    def generate_customer_segments(self) -> pd.DataFrame:
        """Generate customer segments data"""
        print("Generating customer segments...")

        segments_data = []

        for segment_name, segment_info in CUSTOMER_SEGMENTS.items():
            segments_data.append({
                "segment": segment_name,
                "size": segment_info["size"],
                "avg_ltv": segment_info["avg_ltv"],
                "avg_order_value": segment_info["avg_order_value"],
                "purchase_frequency": segment_info["purchase_frequency"],
                "retention_rate": segment_info["retention_rate"],
                "primary_product": segment_info["primary_product"],
                "characteristics": f"Health-focused consumers interested in {segment_info['primary_product']}",
            })

        df = pd.DataFrame(segments_data)
        df.to_csv(self.output_dir / "customer_segments.csv", index=False)
        print(f"✓ Generated {len(df)} customer segments")
        return df

    def generate_competitor_intel(self) -> pd.DataFrame:
        """Generate competitor intelligence data"""
        print("Generating competitor intelligence...")

        competitor_data = []

        for competitor_name, competitor_info in COMPETITORS.items():
            competitor_data.append({
                "competitor": competitor_name,
                "product_category": "Sugar Substitute",
                "price_per_kg": competitor_info["price_per_kg"],
                "market_share_pct": competitor_info["market_share"] * 100,
                "last_updated": END_DATE.date(),
                "strengths": ", ".join(competitor_info["strengths"]),
                "weaknesses": ", ".join(competitor_info["weaknesses"]),
            })

        df = pd.DataFrame(competitor_data)
        df.to_csv(self.output_dir / "competitor_intel.csv", index=False)
        print(f"✓ Generated {len(df)} competitor records")
        return df

    def generate_product_costs(self) -> pd.DataFrame:
        """Generate product costs data"""
        print("Generating product costs...")

        costs_data = []

        for product_name, product_info in PRODUCTS.items():
            costs_data.append({
                "product_name": product_name,
                "cogs_per_kg": product_info["cogs_per_kg"],
                "packaging_cost_per_unit": round(product_info["cogs_per_kg"] * 0.08, 2),
                "distribution_cost_per_kg": round(product_info["cogs_per_kg"] * 0.05, 2),
                "total_variable_cost": round(
                    product_info["cogs_per_kg"] * 1.13, 2
                ),  # COGS + packaging + distribution
                "last_updated": END_DATE.date(),
            })

        df = pd.DataFrame(costs_data)
        df.to_csv(self.output_dir / "product_costs.csv", index=False)
        print(f"✓ Generated {len(df)} product cost records")
        return df

    def generate_revenue_by_channel(self, sales_df: pd.DataFrame) -> pd.DataFrame:
        """Generate aggregated revenue by channel data"""
        print("Generating revenue by channel...")

        # Aggregate sales by month, product, and channel
        sales_df['date'] = pd.to_datetime(sales_df['date'])
        sales_df['month'] = sales_df['date'].dt.to_period('M')

        revenue_data = []

        for (month, product, channel), group in sales_df.groupby(['month', 'product_name', 'pos_type']):
            revenue = group['revenue'].sum()
            cost = group['cost'].sum()
            gross_profit = revenue - cost
            gross_margin_pct = (gross_profit / revenue * 100) if revenue > 0 else 0

            revenue_data.append({
                "month": month.to_timestamp().date(),
                "product_name": product,
                "channel": channel,
                "revenue": round(revenue, 2),
                "cost": round(cost, 2),
                "gross_profit": round(gross_profit, 2),
                "gross_margin_pct": round(gross_margin_pct, 2),
            })

        df = pd.DataFrame(revenue_data)
        df = df.sort_values(["month", "product_name", "channel"]).reset_index(drop=True)
        df.to_csv(self.output_dir / "revenue_by_channel.csv", index=False)
        print(f"✓ Generated {len(df)} revenue records")
        return df

    def generate_all(self):
        """Generate all datasets"""
        print("\n" + "="*60)
        print("BIOLABS DATA GENERATION")
        print("="*60 + "\n")

        # Generate in order (some depend on others)
        self.generate_pos_master()
        sales_df = self.generate_sales_transactions()
        self.generate_inventory_levels()
        self.generate_campaigns()
        self.generate_customer_segments()
        self.generate_competitor_intel()
        self.generate_product_costs()
        self.generate_revenue_by_channel(sales_df)

        print("\n" + "="*60)
        print("✓ ALL DATA GENERATED SUCCESSFULLY")
        print(f"Output directory: {self.output_dir.absolute()}")
        print("="*60 + "\n")

        # Generate summary statistics
        self.print_summary(sales_df)

    def print_summary(self, sales_df: pd.DataFrame):
        """Print summary statistics"""
        print("\nDATA SUMMARY")
        print("-" * 60)

        total_revenue = sales_df['revenue'].sum()
        total_cost = sales_df['cost'].sum()
        total_profit = total_revenue - total_cost

        print(f"Total Transactions: {len(sales_df):,}")
        print(f"Date Range: {sales_df['date'].min()} to {sales_df['date'].max()}")
        print(f"Total Revenue: ${total_revenue:,.2f}")
        print(f"Total Cost: ${total_cost:,.2f}")
        print(f"Total Gross Profit: ${total_profit:,.2f}")
        print(f"Overall Margin: {(total_profit/total_revenue*100):.2f}%")

        print("\nRevenue by Product:")
        for product, group in sales_df.groupby('product_name'):
            revenue = group['revenue'].sum()
            print(f"  {product}: ${revenue:,.2f} ({revenue/total_revenue*100:.1f}%)")

        print("\nRevenue by Channel:")
        for channel, group in sales_df.groupby('pos_type'):
            revenue = group['revenue'].sum()
            print(f"  {channel}: ${revenue:,.2f} ({revenue/total_revenue*100:.1f}%)")

        print("-" * 60)


if __name__ == "__main__":
    generator = BioLabsDataGenerator()
    generator.generate_all()
