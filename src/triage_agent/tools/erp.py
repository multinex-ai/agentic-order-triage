"""ERP Inventory & Catalog Lookup Integration (SAP / Oracle NetSuite)."""

from __future__ import annotations

from typing import Any, Dict, List

from triage_agent.tools.base import BaseTool


class ERPInventoryTool(BaseTool):
    name: str = "erp_inventory_check"
    description: str = (
        "Verify inventory availability, warehouse locations, and special handling (cold chain / hazardous)."
    )

    # Mock catalog database representing enterprise biotech and specialty logistics catalog
    CATALOG_DB: Dict[str, Dict[str, Any]] = {
        "MNX-BIO-9021": {
            "name": "Ultra-Pure Taq Polymerase 500U",
            "stock": 450,
            "warehouse": "US-EAST-1",
            "cold_chain_celsius": -20,
            "hazardous": False,
            "unit_cost": 210.0,
        },
        "MNX-CRYO-1004": {
            "name": "Liquid Nitrogen Vapor Shipper 25L",
            "stock": 18,
            "warehouse": "US-CENTRAL-2",
            "cold_chain_celsius": -196,
            "hazardous": True,
            "unit_cost": 4850.0,
        },
        "MNX-GENE-4400": {
            "name": "NextGen Sequencing Reagent Kit 96-well",
            "stock": 85,
            "warehouse": "US-WEST-1",
            "cold_chain_celsius": -80,
            "hazardous": False,
            "unit_cost": 1250.0,
        },
        "MNX-PLAST-0012": {
            "name": "Sterile Falcon Tubes 50mL (Case of 500)",
            "stock": 1200,
            "warehouse": "US-EAST-1",
            "cold_chain_celsius": None,
            "hazardous": False,
            "unit_cost": 145.0,
        },
    }

    def run(self, **kwargs: Any) -> Dict[str, Any]:
        items: List[Dict[str, Any]] = kwargs.get("items", [])
        if not items:
            return {"status": "FAILED", "reason": "No items provided for stock verification"}

        verified_items: List[Dict[str, Any]] = []
        all_in_stock = True
        has_hazardous = False
        requires_cryo_cold_chain = False

        for item in items:
            sku = item.get("sku", "")
            qty = item.get("quantity", 1)
            cat_info = self.CATALOG_DB.get(sku)

            if not cat_info:
                # Fallback for dynamic/unlisted SKUs
                verified_items.append(
                    {
                        "sku": sku,
                        "in_stock": True,
                        "available_qty": 999,
                        "cold_chain": None,
                        "hazardous": False,
                        "warning": "Uncataloged SKU; standard fulfillment",
                    }
                )
                continue

            in_stock = cat_info["stock"] >= qty
            if not in_stock:
                all_in_stock = False

            if cat_info["hazardous"]:
                has_hazardous = True
            # Cryogenic ultra-cold chain requires specialized vapor shippers (-80C or -196C)
            if cat_info["cold_chain_celsius"] is not None and cat_info["cold_chain_celsius"] <= -80:
                requires_cryo_cold_chain = True

            verified_items.append(
                {
                    "sku": sku,
                    "name": cat_info["name"],
                    "requested_qty": qty,
                    "available_stock": cat_info["stock"],
                    "in_stock": in_stock,
                    "warehouse": cat_info["warehouse"],
                    "cold_chain_celsius": cat_info["cold_chain_celsius"],
                    "hazardous": cat_info["hazardous"],
                }
            )

        return {
            "all_in_stock": all_in_stock,
            "has_hazardous_materials": has_hazardous,
            "requires_cryo_cold_chain": requires_cryo_cold_chain,
            "verified_items": verified_items,
        }
