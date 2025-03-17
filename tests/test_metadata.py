from wapiti_swagger.parser import extract_metadata


def test_extract_metadata():
    input_dict = {
        'info': {
            'title': 'Foo Service',
            'version': 'v1.0'
        },
        'openapi': '3.0.1',
        'servers': [
            {
                'url': 'https://{foo}.com',
                'variables': {
                    'foo': {'default': 'bar'}
                }
            }
        ]
    }

    assert extract_metadata(input_dict) == {"servers": ["https://bar.com"]}
