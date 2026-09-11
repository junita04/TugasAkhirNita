"""
Debug: Check the actual big_number_total viz class and its supported params.
"""
import sys, json
sys.path.insert(0, '/app')
from superset.app import create_app
app = create_app()
app.app_context().push()

# Check viz.py for big_number
from superset import viz
import inspect

# Get all classes that have 'big' in name
for name, cls in inspect.getmembers(viz):
    if 'big' in name.lower():
        print(f"Class: {name}")
        print(f"  Type: {type(cls)}")
        if hasattr(cls, 'viz_id'):
            print(f"  viz_id: {cls.viz_id}")
        if hasattr(cls, 'form_fields'):
            print(f"  form_fields: {cls.form_fields}")
        if hasattr(cls, 'form_data_fields'):
            print(f"  form_data_fields: {cls.form_data_fields}")
        # Check init
        if hasattr(cls, '__init__'):
            sig = inspect.signature(cls.__init__)
            print(f"  init_params: {list(sig.parameters.keys())}")
        print()

# Check the base viz class
print("--- Base viz classes ---")
for name, cls in inspect.getmembers(viz):
    if inspect.isclass(cls) and hasattr(cls, 'viz_id'):
        print(f"  {name}: viz_id={cls.viz_id}")
