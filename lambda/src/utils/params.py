from datetime import datetime

def sales_items_params_builder(start: datetime, end: datetime, limit: int):
    def _builder(offset: int):
        return {
            "p_date_column_filter": "created_at",
            "p_filter_date_start": start.strftime("%Y-%m-%dT%H:%M:%S"),
            "p_filter_date_end": end.strftime("%Y-%m-%dT%H:%M:%S"),
            "p_limit": limit,
            "p_offset": offset,
        }
    return _builder


def inventory_params_builder(
    start: datetime,
    end: datetime,
    limit: int,
):
    def _builder(offset: int):
        return {
            "p_date_column_filter": "created_at",
            "p_filter_date_start": start.strftime("%Y-%m-%dT%H:%M:%S"),
            "p_filter_date_end": end.strftime("%Y-%m-%dT%H:%M:%S"),
            "p_limit": limit,
            "p_offset": offset,
        }
    return _builder


def sales_params_builder(start: datetime, end: datetime, limit: int):
    def _builder(offset: int):
        return {
            "p_date_column_filter": "shift_date",
            "p_filter_date_start": start.strftime("%Y-%m-%dT%H:%M:%S"),
            "p_filter_date_end": end.strftime("%Y-%m-%dT%H:%M:%S"),
            "p_limit": limit,
            "p_offset": offset,
        }
    return _builder
