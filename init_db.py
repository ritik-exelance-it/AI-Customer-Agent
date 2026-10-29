from database.schema import initialize_database


def main():
    initialize_database(seed_demo_data=True)
    print("Database initialized successfully.")
    print("Demo customers and support tickets are ready.")


if __name__ == "__main__":
    main()