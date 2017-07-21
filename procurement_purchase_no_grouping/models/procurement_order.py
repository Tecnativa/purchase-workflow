# -*- coding: utf-8 -*-
# Copyright 2015 AvanzOsc (http://www.avanzosc.es)
# Copyright 2015-2017 - Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from openerp import models, api


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    @api.multi
    def make_po(self):
        po_line = False
        grouping = self.product_id.categ_id.procured_purchase_grouping
        if grouping == 'line':
            # Find previously any possible matched PO line recreating upstream
            # domain and make it to not match changing the UoM of the line
            suppliers = self.product_id.seller_ids.filtered(lambda r: (
                not r.product_id or r.product_id == self.product_id
            ))
            if suppliers:
                supplier = suppliers[0]
                partner = supplier.name
                gpo = self.rule_id.group_propagation_option
                group = (gpo == 'fixed' and self.rule_id.group_id) or \
                        (gpo == 'propagate' and self.group_id) or False
                domain = [
                    ('partner_id', '=', partner.id),
                    ('state', '=', 'draft'),
                    ('picking_type_id', '=', self.rule_id.picking_type_id.id),
                    ('company_id', '=', self.company_id.id),
                    ('dest_address_id', '=', self.partner_dest_id.id),
                ]
                if group:
                    domain += (('group_id', '=', group.id),)
                po = self.env['purchase.order'].search(domain, limit=1)
                for line in po.order_line:
                    if (line.product_id == self.product_id and
                            line.product_uom == self.product_id.uom_po_id):
                        po_line = line
                        po_line_uom = po_line.product_uom
                        virtual_uom = po_line_uom.create(
                            po_line_uom._convert_to_write(
                                po_line_uom._convert_to_cache(
                                    po_line_uom.read()[0]
                                )
                            )
                        )
                        po_line.update({'product_uom': virtual_uom.id})
                        break
            obj = self
        else:
            obj = self.with_context(
                grouping=self.product_id.categ_id.procured_purchase_grouping,
            )
        res = super(ProcurementOrder, obj).make_po()
        if po_line:
            # Restore original UoM
            po_line.update({'product_uom': po_line_uom.id})
            virtual_uom.unlink()
        return res
