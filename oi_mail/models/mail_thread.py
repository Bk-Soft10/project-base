'''
Created on Feb 4, 2021

@author: Zuhair Hammadi
'''
from odoo import models, api
from odoo.tools.misc import clean_context
from odoo.osv.query import Query
import logging

_logger = logging.getLogger(__name__)

class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'            
        
    def _get_db_values(self, fields):
        
        field_names = []
        inherited_field_names = []
        for name in fields:
            field = self._fields.get(name)
            if field:
                if field.store:
                    field_names.append(name)
                elif field.base_field.store:
                    inherited_field_names.append(name)
            else:
                _logger.warning("%s.read() with unknown field '%s'", self._name, name)

        # determine the fields that are stored as columns in tables; ignore 'id'
        fields_pre = [
            field
            for field in (self._fields[name] for name in field_names + inherited_field_names)
            if field.name != 'id'
            if field.base_field.store and field.base_field.column_type
            if not (field.inherited and callable(field.base_field.translate))
        ]
        
        env = self.env
        cr, user, context, su = env.args        # @UnusedVariable
        
        param_ids = object()
        query = Query(['"%s"' % self._table], ['"%s".id IN %%s' % self._table], [param_ids])
        self._apply_ir_rules(query, 'read')

        # the query may involve several tables: we need fully-qualified names
        def qualify(field):
            col = field.name
            res = self._inherits_join_calc(self._table, field.name, query)
            if field.type == 'binary' and (context.get('bin_size') or context.get('bin_size_' + col)):
                # PG 9.2 introduces conflicting pg_size_pretty(numeric) -> need ::cast
                res = 'pg_size_pretty(length(%s)::bigint)' % res
            return '%s as "%s"' % (res, col)

        # selected fields are: 'id' followed by fields_pre
        qual_names = [qualify(name) for name in [self._fields['id']] + fields_pre]

        # determine the actual query to execute
        from_clause, where_clause, params = query.get_sql()
        query_str = "SELECT %s FROM %s WHERE %s" % (",".join(qual_names), from_clause, where_clause)

        # fetch one list of record values per field
        param_pos = params.index(param_ids)

        result = []
        for sub_ids in cr.split_for_in_conditions(self.ids):
            params[param_pos] = tuple(sub_ids)
            cr.execute(query_str, params)
            result += cr.fetchall()
            
        res = {}
        
        for row in result:
            vals = {}
            for field,value in zip(fields_pre, row[1:]):
                vals[field.name] = value
            
            res[row[0]]= self._convert_to_record(vals)
                                    
        return res                        
                
    def _write(self, values):
        if self._context.get('tracking_disable'):
            return super(MailThread, self)._write(values)

        # Track initial values of tracked fields
        track_self = self.with_lang()

        tracked_fields = None
        if not self._context.get('mail_notrack'):
            tracked_fields = track_self._get_tracked_fields_computed(values)
            
        if tracked_fields:
            initial_values = track_self._get_db_values(tracked_fields)
            for record in self:
                vals = initial_values.setdefault(record.id, {})
                for field in tracked_fields:
                    vals.setdefault(field, False)

        # Perform write
        result = super(MailThread, self)._write(values)
        
        # Perform the tracking
        if tracked_fields:
            tracking = track_self.with_context(clean_context(self._context)).message_track(tracked_fields, initial_values)
            if any(change for rec_id, (change, tracking_value_ids) in tracking.items()):  # @UnusedVariable
                (changes, tracking_value_ids) = tracking[track_self[0].id]  # @UnusedVariable
                track_self._message_track_post_template(changes)
        return result
    
    @api.model
    def _get_tracked_fields_computed(self, fnames=None):
        """ Return a structure of tracked fields for the current model.
            :return dict: a dict mapping field name to description, containing on_change fields
        """
        tracked_fields = []
        for name, field in self._fields.items():
            if fnames and name not in fnames:
                continue
            tracking = getattr(field, 'tracking', None) or getattr(field, 'track_visibility', None)
            if tracking and field.compute and field.store:
                tracked_fields.append(name)

        if tracked_fields:
            return self.fields_get(tracked_fields)
        return {}    