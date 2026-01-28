from fastapi import FastAPI

app = FastAPI(title='Third Eye API')

@app.get('/health')
def health():
    return {'status': 'ok'}
