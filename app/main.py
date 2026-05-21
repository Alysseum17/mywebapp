import argparse
import os

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
                <li>GET /items — list of all items</li>
                <li>POST /items — create item</li>
                <li>GET /items/{id} — item details</li>
            </ul>
        </body></html>
        """

    return app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="mywebapp Simple Inventory")
    parser.add_argument("--host", default=os.getenv("APP_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("APP_PORT", "8080")))
    parser.add_argument("--db-host", default=os.getenv("DB_HOST", "127.0.0.1"))
    parser.add_argument("--db-port", type=int, default=int(os.getenv("DB_PORT", "3306")))
    parser.add_argument("--db-user", default=os.getenv("DB_USER"))
    parser.add_argument("--db-password", default=os.getenv("DB_PASSWORD"))
    parser.add_argument("--db-name", default=os.getenv("DB_NAME"))

    parser.add_argument(
        "--fd",
        type=int,
        default=None,
        help="File descriptor from systemd socket activation",
    )

    args = parser.parse_args()

    missing = []
    if not args.db_user:
        missing.append("--db-user / DB_USER")
    if not args.db_password:
        missing.append("--db-password / DB_PASSWORD")
    if not args.db_name:
        missing.append("--db-name / DB_NAME")
    if missing:
        parser.error(f"Missing required: {', '.join(missing)}")

    return args


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

    if args.fd is not None:
        uvicorn.run(app, fd=args.fd)
    else:
        uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
