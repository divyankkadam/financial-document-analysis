from neo4j import GraphDatabase

from app.config import settings


def main():
    print(f"URI: {settings.neo4j_uri}")
    print(f"USER: {settings.neo4j_user}")
    print(f"DATABASE: {settings.neo4j_database}")
    print(f"PASSWORD SET: {bool(settings.neo4j_password)}")

    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    try:
        with driver.session(database=settings.neo4j_database) as session:
            status = session.run("RETURN 'connected' AS status").single()["status"]
            print(status)
    finally:
        driver.close()


if __name__ == "__main__":
    main()
