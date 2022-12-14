#! python3
# -*- coding: utf-8 -*-

import mysql.connector as mc
from mysql.connector import errorcode
import argparse
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common import exceptions

import time


# Process to do -> 1. Se connecter a la base de donnée client
#              -> Selectionner le client spécifier dans le parametre du script
#                   ->Si pas de client alors renvoie "Le client n'existe pas dans la bdd"
#                   ->Sinon si plusieurs client demandé lequel exactement.
#                   -Ouvrir une page web de google maps
#                   ->Accepter les cookiess
#                   -> Et ecrire l'address du client en question
#                   -> Faire l'itinéraire
#                   -> Imprimer l'itinéraire
#                   Done


def get_address(client):
    """
    Get the different parameters that are in the cell and give an address that can be browsed .

    :pre: The client must have an address that exists
    :post: Return a string with de concatenation of the ADRESSE and LOCALITE of the client .
    :param client: tuple which must contain in this order the CLIENT NUMBER, NAME, ADDRESS, LOCALITY
    :return: return the concatenation with a space of the address as well as the locality
    """
    address = str(client[2]) + ' ' + str(client[3])
    return address


def get_googlemaps(address, name="Unknown"):
    """
    Take a screenshot of the route from Ephec to the client's address and add it to the folder where its run as png

    :pre:The address must be a real address
    :post: Based on the customer's name, creates a png file in the format "route of
    %CUSTOMERNAME%.png" with the fastest route from a certain location.

    :param address: address of the person in real life. Must exist
    :param name: the name of the client
    :return: 1 if the screenshot when through without error
    :raise error: If the browser is too slow (due to internet connection  or something else) the driver will not find
     the elements resulting in a bad screenshot or in an error if that occur, we leave the program
     """
    driver = webdriver.Chrome()
    try:
        driver.implicitly_wait(10)
        driver.get("https://google.be/maps")
        # Laisse le temps a la page de charger
        # Clique sur accepter quand la popup viens
        popup = driver.find_element(By.XPATH,
                                    "/html/body/c-wiz/div/div/div/div[2]/div[1]/div[3]/div[1]/div[1]/form[2]"
                                    "/div/div/button")
        popup.click()

        # Attends que ça charge
        time.sleep(2)
        # Cherche la barre de recherche
        search_bar = driver.find_element(By.ID, "searchboxinput")
        # address
        search_bar.send_keys(address)
        search_bar.send_keys(Keys.RETURN)
        # Fais l'itinéraire avec l'Ephec
        itin = driver.find_element(By.XPATH,
                                   "//*[@id=\"QA0Szd\"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[4]/div[1]/button")
        itin.click()
        time.sleep(2)
        search_bar_iti = driver.find_element(By.XPATH, "//*[@id=\"sb_ifc51\"]/input")
        search_bar_iti.send_keys("Ephec LLN")
        driver.find_element(By.XPATH, "//*[@id=\"directions-searchbox-0\"]/button[1]").click()
        time.sleep(2)
        # Prend le temps que ça mettrait pour arriver jusqu'au client depuis l'Ephec
        temps = driver.find_element(By.XPATH, "//*[@id=\"section-directions-trip-0\"]/div[1]")
        temps.click()
        time.sleep(4)
        plan = driver.find_element(By.XPATH, "//*[@id=\"QA0Szd\"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]")
        plan.screenshot(f"./itinéraire_to_{str(name)}.png")
        return 1
    except exceptions as err:
        print(err)
        exit(2)
    finally:
        # Ferme le naviguateur
        driver.close()


def find_to_db(db_user, db_password, client_name, db_name="test"):
    """
    :pre: the db must have a table client with those 4 columns, NCLI, NOM, ADRESSE, LOCALITE
    :post: Return a table of tuples of the different clients that have the corresponding name
     containing each in this form [(NCLI,NOM,ADRESSE,LOCALITE)(NCLI,NOM,ADRESSE,LOCALITE)]
    :param db_user: the username to connect to the db
    :param db_password: the password associated with the @db_user
    :param client_name: the client name that we seek
    :param db_name: The name of the db that we will connect in this case, test
    :return: A list of tuple contaning the result of the query
    :raises AccessDeniedException if the credentials are wrong or a Bad_Db_Error if the name of the db is incorrect
    """
    try:
        # Connection a la db sur mon pc
        cnx = mc.connect(user=db_user,
                         password=db_password,
                         host='127.0.0.1',
                         database=db_name)
        # Crée un curseur pour executer la query
        cursor = cnx.cursor()
        # On prend ce qui nous interresse
        fields = "NCLI, NOM, ADRESSE, LOCALITE"
        table = "client"
        conditions = "NOM = %s"
        query = (f"SELECT {fields} "
                 f"FROM {table} "
                 f"WHERE {conditions};")

        cursor.execute(query, client_name)

        myresult = cursor.fetchall()
        cnx.close()
        return myresult
    except mc.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password please "
                  "look for the right credentials")
            exit(2)
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
            exit(2)
        else:
            print(err)
            exit(2)


def many_client(many):
    """
    PRE: many must be an iterable object
    POST: return only and only one client given the client number OR exit the program if they don't rememeber it
    :raise
    :param many: The table of client that we need to sort
    :return:
    """
    if len(many) > 1:
        print("There is more than one client with that name \n, please provide your unique client number\n")
        client = ()
        ok = 0
        while ok < 1:
            ncli = input("What is your client number ?\n")
            for x in many:
                if ncli.upper() in x[0].upper():
                    client = x
                    ok = 1
            if not ok:
                print("There is no such client number for the name you provide\n")
                suite = 1
                while suite == 1:
                    again = input("Would you like to retype ? press y for yes or n for no\n")
                    if again == 'n':
                        print("Please search for another name and come back")
                        exit(1)
                    elif again == 'y':
                        suite = 0

    else:
        client = many[0]

    return client


def main():
    parser = argparse.ArgumentParser(
        description="Look for a client in the database and open a browser with "
                    "google maps and create a png with the directions to go to his house",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    requiredNamed = parser.add_argument_group('required named arguments')
    parser.add_argument("-c", "--client", help="Name of the client")
    requiredNamed.add_argument("-p", "--password", help="Password for access of the database", required=True)
    requiredNamed.add_argument("-u", "--user", help="Username for access of the database", required=True)
    parser.add_argument("-dbn", "--dbname", help="Name of the database you try to access , default is test",
                        default="test")
    args = parser.parse_args()

    result = find_to_db(args.user, args.password, [args.client], args.dbname)
    if not result:
        print(f"There is no client {args.client} in the database sorry")
        exit(1)

    # Case of many clients with the same name, ask for the client number.
    client_unique = many_client(result)
    # now open a window with selenium and search for Google Maps
    a = get_googlemaps(get_address(client_unique), client_unique[1])
    if a == 1:
        print("Succefull ! You can find the itinerary in this folder")


if __name__ == '__main__':
    main()



