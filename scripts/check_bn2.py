import sys, json
sys.path.insert(0, '/app')
from superset.app import create_app
app = create_app()
app.app_context().push()

from superset import db
from superset.models.slice import Slice

# Get chart 145 current config
s = db.session.query(Slice).get(145)
if s:
    print(f"Chart 145: {s.slice_name}")
    print(f"viz_type: {s.viz_type}")
    params = json.loads(s.params) if s.params else {}
    print(f"Current params: {json.dumps(params, indent=2)}")

# Check what the big_number chart class looks like
from superset.viz import viz_types
print(f"\nAvailable viz_types with 'big': {[k for k in viz_types if 'big' in k.lower()]}")

# Try to get the viz class
for name, cls in viz_types.items():
    if name and 'big' in name.lower():
        print(f"\nViz class: {name}")
        print(f"  Type: {type(cls)}")
        if hasattr(cls, '__init__'):
            import inspect
            sig = inspect.signature(cls.__init__)
            print(f"  Init params: {list(sig.parameters.keys())}")
