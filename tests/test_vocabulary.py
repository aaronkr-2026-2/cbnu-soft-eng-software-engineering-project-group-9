from fastapi.testclient import TestClient
from cospeaklocal.app import app, sign_dictionary


def test_public_vocabulary_matches_active_dictionary():
    client = TestClient(app)
    response = client.get('/api/dictionary')
    assert response.status_code == 200
    data = response.json()
    assert set(data) == {'words', 'count'}
    assert data['words'] == sorted(sign_dictionary().by_gloss)
    assert data['count'] == len(data['words'])
    assert 'coffee' in data['words']
    assert 'thank you' in data['words']
    for word in data['words']:
        assert all(m.meta is not None for m in sign_dictionary().plan(word))


def test_dictionary_ui_is_served():
    client = TestClient(app)
    assert 'id="word-search"' in client.get('/').text
    assert client.get('/dictionary.js').status_code == 200
