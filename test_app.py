import pytest
import app
from server_flask import server

def test_clean_text():
    """Memastikan teks kotor HTML dan simbol aneh bisa dibersihkan"""
    teks_kotor = "<p>Halo!!! Ini diskon 50% @#$</p>"
    hasil = app.clean_text(teks_kotor)
    
    assert "Halo!!! Ini diskon 50%" in hasil
    assert "<p>" not in hasil

@pytest.fixture
def client():
    server.config['TESTING'] = True
    with server.test_client() as client:
        yield client

def test_homepage(client):
    """Memastikan halaman utama bisa diakses (Status 200 OK)"""
    
    with client.session_transaction() as sess:
        sess['logged_in'] = True
        sess['user_name'] = 'TestUser'

    response = client.get('/chat')
    
    assert response.status_code == 200
    assert b"AI Agents UI" in response.data

def test_api_products(client):
    """Memastikan API JSON berjalan dengan baik"""
    response = client.get('/api/products')
    
    assert response.status_code == 200
    assert response.is_json
    
    data = response.get_json()
    assert data["status"] == "success"
    assert "total_products" in data

def test_submit_feedback(client):
    """Memastikan fitur tombol jempol up/down berfungsi dan tersimpan"""
    
    client.post('/api/chat', json={'message': 'Tolong rekomendasikan laptop'})
    
    data_feedback = {
        "chat_index": 0,
        "feedback": "up"
    }
    
    response = client.post('/submit_feedback', json=data_feedback)
    
    assert response.status_code == 200
    
    data = response.get_json()
    assert data["status"] == "success"