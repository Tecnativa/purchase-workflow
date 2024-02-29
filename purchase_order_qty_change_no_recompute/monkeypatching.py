# Copyright 2023 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.fields import Field

get_depends_original = Field.get_depends


def get_depends(self, model):
    """Override of the Python method to remove the dependency of the unit fields.
    We also need to add the name and date_planned fields because they use the same
    compute method as the price_unit field."""
    depends, depends_context = get_depends_original(self, model)
    if model._name == "purchase.order.line" and self.name in {
        "name",
        "date_planned",
        "price_unit",
        "discount",
    }:
        if "product_qty" in depends:
            depends.remove("product_qty")
        if "product_uom" in depends:
            depends.remove("product_uom")
        # We need to add a field to the depends to be defined.
        if self.name == "date_planned":
            depends.append("product_id")
    return depends, depends_context


# Monkey-patching of the method
Field.get_depends = get_depends
