from fastapi import FastAPI
from sqlalchemy import create_engine, text

app = FastAPI()

engine = create_engine("sqlite:///inventory.db")

@app.get("/api/companies/{company_id}/alerts/low-stock")
def give_alerts(company_id: int):
    sql_query = """
        WITH recent_sold_product_dates AS (
            SELECT 
                ps.id AS product_id,
                ps.name,
                MAX(sa.sale_date) AS recent_date
            FROM products ps
            JOIN sales sa ON sa.product_id = ps.id
            WHERE ps.company_id = :company_id
            GROUP BY ps.id, ps.name
        ),
        recently_sold_products AS (
            SELECT name
            FROM recent_sold_product_dates
            WHERE recent_date >= DATE('now', '-90 day')
        ),
        products_sold_each_month AS (
            SELECT 
                p.id AS product_id,
                strftime('%m', sa.sale_date) AS sale_month,
                COUNT(*) AS total_sold
            FROM sales sa
            JOIN products p ON p.id = sa.product_id
            GROUP BY p.id, sale_month
        ),
        products_sold_each_day AS (
            SELECT 
                product_id,
                SUM(total_sold) / 365.0 AS sold_per_day
            FROM products_sold_each_month
            GROUP BY product_id
        )
        SELECT 
            ps.id AS product_id,
            ps.name AS product_name,
            ps.sku,
            wa.id AS warehouse_id,
            wa.name AS warehouse_name,
            inven.available_stock AS current_stock,
            al.threshold,
            (inven.available_stock / NULLIF(psed.sold_per_day, 0)) AS days_until_stockout,
            sup.id AS supplier_id,
            sup.name AS supplier_name,
            sup.email AS supplier_email
        FROM products ps
        JOIN inventory inven ON ps.id = inven.product_id
        JOIN warehouses wa ON wa.id = inven.warehouse_id
        JOIN alerts al ON al.product_id = ps.id
        JOIN suppliers sup ON sup.id = ps.supplier_id
        LEFT JOIN products_sold_each_day psed ON psed.product_id = ps.id
        WHERE ps.name IN (SELECT name FROM recently_sold_products)
        AND inven.available_stock < al.threshold;
    """

    with engine.connect() as conn:
        results = conn.execute(text(sql_query), {"company_id": company_id})

        alerts = [
            {
                "product_id": row.product_id,
                "product_name": row.product_name,
                "sku": row.sku,
                "warehouse_id": row.warehouse_id,
                "warehouse_name": row.warehouse_name,
                "current_stock": row.current_stock,
                "threshold": row.threshold,
                "days_until_stockout": row.days_until_stockout,
                "supplier": {
                    "id": row.supplier_id,
                    "name": row.supplier_name,
                    "contact_email": row.supplier_email
                }
            }
            for row in results
        ]

    return {"alerts": alerts, "total_alerts": len(alerts)}