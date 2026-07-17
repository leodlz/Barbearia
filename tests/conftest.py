from collections.abc import Generator

import pytest
import os
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import Base, get_db
from app.models import agendamento  # noqa: F401
from app.routes.agendamentos import router as agendamentos_router
from app.routes.admin_auth import router as admin_auth_router
from app.routes.admin import router as admin_router
from app.routes.barbeiros import router as barbeiros_router
from app.routes.clientes import router as clientes_router
from app.routes.disponibilidade import router as disponibilidade_router
from app.routes.servicos import router as servicos_router
from app.models.usuario_master import UsuarioMaster
from app.services.cliente_service import gerar_hash


@pytest.fixture
def session_factory() -> Generator[sessionmaker[Session], None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    with testing_session() as db:
        db.add(UsuarioMaster(nome="Admin", usuario="Admin", senha_hash=gerar_hash("senha-admin"), papel="master", ativo=True))
        db.commit()

    yield testing_session

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def client(session_factory: sessionmaker[Session]) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="teste")
    app.include_router(agendamentos_router)
    app.include_router(barbeiros_router)
    app.include_router(servicos_router)
    app.include_router(disponibilidade_router)
    app.include_router(clientes_router)
    app.include_router(admin_auth_router)
    app.include_router(admin_router)
    app.dependency_overrides[get_db] = override_get_db

    os.environ["ADMIN_API_KEY"] = "teste-admin"
    with TestClient(app, headers={"X-Admin-Key": "teste-admin"}) as test_client:
        login = test_client.post("/api/admin/login", json={"usuario": "Admin", "senha": "senha-admin"})
        assert login.status_code == 200
        yield test_client
