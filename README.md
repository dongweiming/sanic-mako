# sanic-mako
Mako support for sanic

## Installation

`python3 -m pip install sanic-mako`

## Features

`sanic-mako` supports:

- `@mako.template` syntax
- use `render_template_def` render a specific def from a given template
- use `render_template` render a template from the template folder with the given context
- factory pattern `init_app` method for creating apps

## Usage

```python

from sanic import Sanic
from sanic.response import json 
from sanic_mako import SanicMako

app = Sanic()

mako = SanicMako(app)
# or setup later
# mako = SanicMako()
# mako.init_app(app)

@app.route('/')
@mako.template('index.html')  # decorator method is staticmethod
async def index(request):
    return {'greetings': 'Hello, sanic!'}
    

@bp.route('/login', methods=['GET', 'POST'])
async def login(request):
    error = None
    return await render_template('admin/login_user.html', request,
                                 {'error': error})
                                 
                                 
@bp.route('/post/<post_id>/react', methods=['POST', 'DELETE'])
async def react(request, post_id):
    # ...
    return json({ 'r': 0, 'html': await render_template_def(
                      'utils.html', 'render_react_container', request,
                      {'reaction_type': reaction_type }) })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
```
