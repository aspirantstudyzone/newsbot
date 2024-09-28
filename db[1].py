import aiosqlite

class DatabaseUser:
    def __init__(self, db_name="database.db"):
        self.db_name = db_name

    async def create_table(self):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS Prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    food REAL,
                    coal REAL,
                    oil REAL,
                    uranium REAL,
                    iron REAL,
                    bauxite REAL,
                    lead REAL,
                    gasoline REAL,
                    munitions REAL,
                    steel REAL,
                    aluminum REAL
                )
            """)
            await db.commit()

    async def add_trade_price(self, food, coal, oil, uranium, iron, bauxite, lead, gasoline, munitions, steel, aluminum):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("INSERT INTO Prices (food, coal, oil, uranium, iron, bauxite, lead, gasoline, munitions, steel, aluminum) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                             (food, coal, oil, uranium, iron, bauxite, lead, gasoline, munitions, steel, aluminum))
            await db.commit()

    async def get_latest_trade_prices(self):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute("SELECT * FROM Prices ORDER BY id DESC LIMIT 1") as cursor:
                return await cursor.fetchone()