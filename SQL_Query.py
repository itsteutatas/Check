import datetime
import time
import asyncio
import aiomysql
import sql.dbconfig as dbcfg
import sql.DataBase_setup as dbsetup

class data_adder():

    def __init__(self):
        self.setup = dbsetup.setup()
    
    async def table_name(self):
        # Gets the current date
        table_today = datetime.date.today().strftime("%Y_%m_%d")

        # Adds the date to our database table of the day name
        table_name = f"parkeret_{table_today}"
        return table_name
    
    async def daily_regi(self, plate):
        # Creates daily table if it doesn't already exist.
        await dbsetup.setup.make_table(self.setup)
        # Connects to the database
        conn = await aiomysql.connect(dbcfg.localconfig["host"], dbcfg.localconfig["user"],
                                      dbcfg.localconfig["password"], dbcfg.localconfig["db"])
        curr = await conn.cursor()
        today = str(datetime.date.today().strftime("%Y_%m_%d"))

        await curr.execute(f"INSERT INTO {await self.table_name()} VALUES (0, %s, %s)", (plate, today))

        await conn.commit()
        conn.close()


    async def longterm_regi_update(self, plate):
        conn = await aiomysql.connect(dbcfg.localconfig["host"], dbcfg.localconfig["user"],
                                      dbcfg.localconfig["password"], dbcfg.localconfig["db"])
        curr = await conn.cursor()
        today = str(datetime.date.today().strftime("%Y_%m_%d"))

        await curr.execute("SELECT * FROM System_Regi WHERE NumberPlate = %s", (plate))
        result = await curr.fetchone()

        if result is not None:
            await curr.execute(f"UPDATE System_Regi SET Regi_date = %s WHERE NumberPlate = %s", (today, plate))

            await conn.commit()
            conn.close()
            return result[2]
        else:
            return None


    async def longterm_regi_add(self, email, plate):
        conn = await aiomysql.connect(dbcfg.localconfig["host"], dbcfg.localconfig["user"],
                                      dbcfg.localconfig["password"], dbcfg.localconfig["db"])
        curr = await conn.cursor()
        await curr.execute("SELECT * FROM System_Regi WHERE NumberPlate = %s", (plate))
        result = await curr.fetchone()

        if result is None:
            today = str(datetime.date.today().strftime("%Y_%m_%d"))
            await curr.execute(f"INSERT INTO System_Regi(id, NumberPlate, email, Regi_Date) VALUES (0, %s, %s, %s)", (plate, email, today))

            await conn.commit()
            conn.close()

        else:
            await curr.execute(f"UPDATE System_Regi SET email = %s WHERE NumberPlate = %s", (email, plate))
            print(f"UPDATE System_Regi SET email = %s WHERE NumberPlate = %s", (email, plate))
            await conn.commit()
            conn.close()

    async def add_admin(self, adminuser, password):
        conn = await aiomysql.connect(dbcfg.localconfig["host"], dbcfg.localconfig["user"],
                                      dbcfg.localconfig["password"], dbcfg.localconfig["db"])
        curr = await conn.cursor()
        await curr.execute(f"INSERT INTO SyS_admin(id, username, passwd) VALUES(0, %s, %s)", (adminuser, password))

        await conn.commit()
        conn.close()

    async def del_admin(self, adminuser):
        conn = await aiomysql.connect(dbcfg.localconfig["host"], dbcfg.localconfig["user"],
                                      dbcfg.localconfig["password"], dbcfg.localconfig["db"])
        curr = await conn.cursor()

        await curr.execute(f"DELETE FROM SyS_admin WHERE username = %s", adminuser)

        await conn.commit()
        conn.close()

    async def teacher_add(self, email, plate):
        conn = await aiomysql.connect(dbcfg.localconfig["host"], dbcfg.localconfig["user"],
                                      dbcfg.localconfig["password"], dbcfg.localconfig["db"])
        curr = await conn.cursor()

        today = str(datetime.date.today().strftime("%Y_%m_%d"))
        await curr.execute(f"INSERT INTO Teacher(id, NumberPlate, email, Regi_Date) VALUES (0, %s, %s, %s)", (plate, email, today))

        await conn.commit()
        conn.close()


class data_lookup():

    def __init__(self):
        pass

    async def daily_startup(self):
        conn = await aiomysql.connect(dbcfg.localconfig["host"], dbcfg.localconfig["user"],
                                      dbcfg.localconfig["password"], dbcfg.localconfig["db"])
        curr = await conn.cursor()

        await curr.execute("SHOW TABLES LIKE 'parkeret%'")
        tables = await curr.fetchall()
        statement = ""
        i = 0
        for table in tables:
            i += 1
            statement += "SELECT * FROM "
            statement += str(table[0])
            if i == len(tables):
                pass
            else:
                statement += " UNION "
        statement = statement.strip()
        await curr.execute(statement)
        results = await curr.fetchall()
        
        conn.close()
        return results
    
    async def statementBuilder(self, clause):
        conn = await aiomysql.connect(dbcfg.localconfig["host"], dbcfg.localconfig["user"],
                                      dbcfg.localconfig["password"], dbcfg.localconfig["db"])
        curr = await conn.cursor()

        await curr.execute("SHOW TABLES LIKE 'parkeret%'")
        tables = await curr.fetchall()
        statement = ""
        i = 0
        for table in tables:
            i += 1
            statement += "SELECT * FROM "
            statement += str(table[0])
            statement += f" {clause}"
            if i == len(tables):
                pass
            else:
                statement += "UNION "
        statement = statement.strip()
        return statement, i

    async def daily_lookup(self, search_date, search_plate):
        conn = await aiomysql.connect(dbcfg.localconfig["host"], dbcfg.localconfig["user"],
                                      dbcfg.localconfig["password"], dbcfg.localconfig["db"])
        curr = await conn.cursor()

        if search_date == '':
            if search_plate == '':
                statement, counter = await self.statementBuilder(self, clause='')
                await curr.execute(statement)
                results = await curr.fetchall()
                await curr.execute(f"SELECT * FROM teacher")
                results = results + await curr.fetchall()
            else:
                statement, counter = await self.statementBuilder(self, clause="WHERE NumberPlate = %s ") # Remember space after
                await curr.execute(statement, (search_plate, ) * counter)
                results = await curr.fetchall()
                await curr.execute(f"SELECT * FROM teacher WHERE NumberPlate = %s", (search_plate))
                results = results + await curr.fetchall()

        else:
            if search_plate == '':
                statement, counter = await self.statementBuilder(self, clause="WHERE Del_Date LIKE %s ") # Remember space after
                await curr.execute(statement, (search_date, ) * counter)
                results = await curr.fetchall()
                await curr.execute(f"SELECT * FROM teacher WHERE Regi_Date LIKE %s", (search_date))
                results = results + await curr.fetchall()
            else:
                statement, counter = await self.statementBuilder(self, clause="WHERE Del_Date LIKE %s AND NumberPlate = %s ") # Remember space after
                await curr.execute(statement, (search_date, search_plate) * counter)
                results = await curr.fetchall()
                await curr.execute(f"SELECT * FROM teacher WHERE Regi_Date LIKE %s AND NumberPlate = %s", (search_date, search_plate))
                results = results + await curr.fetchall()

        conn.close()
        return results

    async def regi_lookup(self, search_date, search_plate):
        conn = await aiomysql.connect(dbcfg.localconfig["host"], dbcfg.localconfig["user"],
                                      dbcfg.localconfig["password"], dbcfg.localconfig["db"])
        curr = await conn.cursor()

        if search_date == '':
            if search_plate == '':
                await curr.execute(f"SELECT * FROM System_Regi")
                results = await curr.fetchall()
                await curr.execute(f"SELECT * FROM teacher")
                results = results + await curr.fetchall()
            else:
                await curr.execute(f"SELECT * FROM System_Regi WHERE NumberPlate = %s", (search_plate))
                results = await curr.fetchall()
                await curr.execute(f"SELECT * FROM teacher WHERE NumberPlate = %s", (search_plate))
                results = results + await curr.fetchall()

        else:
            if search_plate == '':
                await curr.execute(f"SELECT * FROM System_Regi WHERE Regi_date LIKE %s", (search_date))
                results = await curr.fetchall()
                await curr.execute(f"SELECT * FROM teacher WHERE Regi_date LIKE %s", (search_date))
                results = results + await curr.fetchall()
            else:
                await curr.execute(f"SELECT * FROM System_Regi WHERE Regi_date LIKE %s AND NumberPlate = %s", (search_date, search_plate))
                results = await curr.fetchall()
                await curr.execute(f"SELECT * FROM teacher WHERE Regi_date LIKE %s AND NumberPlate = %s", (search_date, search_plate))
                results = results + await curr.fetchall()


        conn.close()
        return results

    async def sys_regi_lookup(self, search_plate):
        conn = await aiomysql.connect(dbcfg.localconfig["host"], dbcfg.localconfig["user"],
                                      dbcfg.localconfig["password"], dbcfg.localconfig["db"])
        curr = await conn.cursor()

        if search_plate == None:
            await curr.execute(f"SELECT * FROM System_Regi")
            results = await curr.fetchall()
            await curr.execute(f"SELECT * FROM teacher")
            results = results + await curr.fetchall()
        else:
            await curr.execute(f"SELECT * FROM System_Regi WHERE NumberPlate = %s", (search_plate))
            results = await curr.fetchall()
            await curr.execute(f"SELECT * FROM teacher WHERE NumberPlate = %s", (search_plate))
            results = results + await curr.fetchall()

        curr.close()
        return results

    async def todays_table(self):
        conn = await aiomysql.connect(dbcfg.localconfig["host"], dbcfg.localconfig["user"],
                                      dbcfg.localconfig["password"], dbcfg.localconfig["db"])
        curr = await conn.cursor()

        await curr.execute(f"SELECT * FROM {await self.table_name()}")
        results = await curr.fetchall()
        await curr.execute(f"SELECT * FROM teacher")
        results = results + await curr.fetchall()

        conn.close()
        return results

    async def table_name(self):
        # Gets the current date
        table_today= datetime.date.today().strftime("%Y_%m_%d")

        # Adds the date to our database table of the day name
        table_name = f"parkeret_{table_today}"
        return table_name

    async def admin_check(self, user):

        await dbsetup.setup.make_table(dbsetup.setup())

        conn = await aiomysql.connect(dbcfg.localconfig["host"], dbcfg.localconfig["user"],

                                      dbcfg.localconfig["password"], dbcfg.localconfig["db"])
        curr = await conn.cursor()

        await curr.execute(f"SELECT username FROM SyS_admin WHERE username = %s", (user))
        adminuser = await curr.fetchone()
        await curr.execute(f"SELECT passwd FROM SyS_admin WHERE username = %s", (user))
        password = await curr.fetchone()
        conn.close()
        if adminuser is not None:
            return adminuser[0], password[0].decode('utf-8')
        else:
            return None, None
        


