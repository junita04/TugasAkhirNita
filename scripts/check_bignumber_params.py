import sys, json
sys.path.insert(0, '/app')
from superset.app import create_app
app = create_app()
app.app_context().push()

# Check big_number_total chart class for available params
from superset.viz import viz_types

# Check if big_number_total is a native chart
from superset.explore.form_data.utils import get_form_data_from_chart

# Try to find the viz class
from superset import db
from superset.models.slice import Slice

# Get chart 145 params
s = db.session.query(Slice).get(145)
if s:
    print(f"Chart 145: {s.slice_name}")
    print(f"viz_type: {s.viz_type}")
    print(f"params: {s.params}")
    print()

# Check what the big_number viz supports
# In Superset, big_number_total is a plugin chart
# Let me check the viz.py for big_number
try:
    from superset.viz import BigNumberTotalViz
    print("BigNumberTotalViz found")
    if hasattr(BigNumberTotalViz, 'form_fields'):
        print(f"Form fields: {BigNumberTotalViz.form_fields}")
except ImportError:
    print("BigNumberTotalViz not found in viz.py")

# Check the viz.py file for big number
import inspect
from superset import viz
for name, obj in inspect.getmembers(viz):
    if 'big' in name.lower() or 'number' in name.lower():
        print(f"Found: {name}")
        if hasattr(obj, 'form_fields'):
            print(f"  form_fields: {obj.form_fields}")
