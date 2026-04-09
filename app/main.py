import argparse

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from app import database
from app.routers import health, items


def create_app() -> FastAPI:
    app = FastAPI(title="mywebapp", version="0.1.0")

    app.include_router(health.router)
    app.include_router(items.router)

    @app.get("/", response_class=HTMLResponse)
    def root(request: Request):
        return """
        <html><body>
            <h1>mywebapp — Simple Inventory</h1>
            <h2>Endpoints:</h2>
            <ul>
                <li>GET /items — список всіх предметів</li>
                <li>POST /items — створити предмет</li>
                <li>GET /items/{id} — деталі предмету</li>
            </ul>
        </body></html>
        """

    return app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="mywebapp Simple Inventory")
    parser.add_argument("--host", default="127.0.0.1", help="App host")
    parser.add_argument("--port", type=int, default=8080, help="App port")
    parser.add_argument("--db-host", default="127.0.0.1")
    parser.add_argument("--db-port", type=int, default=3306)
    parser.add_argument("--db-user", required=True)
    parser.add_argument("--db-password", required=True)
    parser.add_argument("--db-name", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    database.init_db(
        host=args.db_host,
        port=args.db_port,
        user=args.db_user,
        password=args.db_password,
        database=args.db_name,
    )

    app = create_app()
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
