#import necessary library that exists in lab machine.
import sqlite3
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import XMLParser, TreeBuilder

#ask user for input, name of database and the inputfile.
x = input("Enter name of database you wish to create: ")
y = input("Enter inputfile name: ")

#declare necessary connection to sqlite3
#connection = sqlite3.connect("heesoo.db")
connection = sqlite3.connect(x)
cursor = connection.cursor()
inputfile = y
tree = ET.parse(y)
#inputfile = 'quad_and_comp_sci.osm.xml'
#tree = ET.parse('quad_and_comp_sci.osm.xml')
root = tree.getroot()

#drop all the tables that I will create, for repetitive run.
def droptable():
    cursor.execute("DROP TABLE IF EXISTS node;")
    cursor.execute("DROP TABLE IF EXISTS way;")
    cursor.execute("DROP TABLE IF EXISTS waypoint;")
    cursor.execute("DROP TABLE IF EXISTS nodetag;")
    cursor.execute("DROP TABLE IF EXISTS waytag;")

#create all the tables needed and commit
def createtable():
    cursor.execute("CREATE TABLE node (id integer, lat float, lon float, PRIMARY KEY(id));")
    cursor.execute("CREATE TABLE way (id integer, closed boolean, PRIMARY KEY(id));")
    cursor.execute("CREATE TABLE waypoint (wayid integer, ordinal integer, nodeid integer, CONSTRAINT fk_wayid FOREIGN KEY (wayid) REFERENCES way(id), CONSTRAINT fk_nodeid FOREIGN KEY (nodeid) REFERENCES node(id));")
    cursor.execute("CREATE TABLE nodetag (id integer, k text, v text, CONSTRAINT fk_nodetag FOREIGN KEY(id) REFERENCES node(id));")
    cursor.execute("CREATE TABLE waytag (id integer, k text, v text, CONSTRAINT fk_waytag FOREIGN KEY(id) REFERENCES way(id));")
    connection.commit()

#insert node with correct constraints and parameters
def insertnode(nodeid, lat, lon):
    cursor.execute('''INSERT INTO node VALUES (:nodeid, :lat, :lon);''',{'nodeid':nodeid, 'lat':lat, 'lon':lon})
    connection.commit()

#insert way with correct constraints and parameters
def insertway(wayid, closed):
    cursor.execute('''INSERT INTO way VALUES (:wayid, :closed);''',{'wayid':wayid, 'closed':closed})
    connection.commit()

#insert waypoint with correct constraints and parameters
def insertwaypoint(wayid, ordinal, nodeid):
    cursor.execute('''INSERT INTO waypoint VALUES (:wayid, :ordinal, :nodeid);''',{'wayid':wayid, 'ordinal':ordinal, 'nodeid':nodeid})
    connection.commit()

#insert nodetag with correct constraints and parameters
def insertnodetag(node_id, k, v):
    cursor.execute('''INSERT INTO nodetag VALUES (:id, :k, :v);''',{'id':node_id, 'k':k, 'v':v})
    connection.commit()

#insert waytag with correct constraints and parameters
def insertwaytag(way_id, k, v):
    cursor.execute('''INSERT INTO waytag VALUES (:id, :k, :v);''',{'id':way_id, 'k':k, 'v':v})
    connection.commit()

#If first element and last element of the list of nd are same, than we update the way to be closed,
#if first elemnt and last element of the list of nd are not same, than we update the way to be open.
def updateclosed(wayid, closedlist):
    if closedlist[0] == closedlist[-1]:
        closed = True
        cursor.execute('''UPDATE way SET closed = :closed WHERE id = :wayid;''',{'closed':closed, 'wayid': wayid})
        connection.commit()
    else:
        closed = False
        cursor.execute('''UPDATE way SET closed = :closed WHERE id = :wayid;''',{'closed':closed, 'wayid': wayid})
        connection.commit()

#Parse the xml file and iterate through the start and end of every line to get necessary data.
def executenode():
    for event, elem in ET.iterparse(inputfile, events=('start', 'end', 'start-ns', 'end-ns')):
        if elem.tag == 'node':
            if elem.tag == 'node' and event == 'start':
                nodeid = elem.attrib['id']
                lat = elem.attrib['lat']
                lon = elem.attrib['lon']
                #once the data are extracted for node, than I insert node and commit.
                insertnode(nodeid, lat, lon)
                connection.commit()
            elif elem.tag == 'node' and event == 'end' and nodeid == elem.attrib['id']:
                #print("MATCH")
                continue

#Parse the xml file and iterate through the start and end of every line to get necessary data.
def executeway():
    closedlist = []
    for event, elem in ET.iterparse(inputfile, events=('start', 'end', 'start-ns', 'end-ns')):
        if elem.tag == 'way':
            if elem.tag == 'way' and event == 'start':
                wayid_for_closed = elem.attrib['id']
                wayroot = elem
                closed = 'NA'
                insertway(wayid_for_closed, closed)
                connection.commit()

                for elem in wayroot:
                    if elem.tag == 'nd':
                        #append all the node from start of way to end of way in a list so we can determine closed or open path.
                        closedlist.append(elem.attrib['ref'])
            elif elem.tag == 'way' and event == 'end' and wayid_for_closed == elem.attrib['id']:
                #once end of way is met, we update with the corresponding list.
                updateclosed(wayid_for_closed, closedlist)
                connection.commit()
                closedlist = []

def executewaypoint():
    pointlist = []
    for event, elem in ET.iterparse(inputfile, events=('start', 'end', 'start-ns', 'end-ns')):
        if elem.tag == 'way':
            if elem.tag == 'way' and event == 'start':
                wayid_for_point = elem.attrib['id']
                wayroot = elem
                for elem in wayroot:
                    if elem.tag == 'nd':
                        #append all the nd from start of way to end of way to determine ordinal.
                        pointlist.append(elem.attrib['ref'])

            elif elem.tag == 'way' and event == 'end' and wayid_for_point == elem.attrib['id']:
                for x in range(len(pointlist)):
                    #from the list we match nd to corresponding wayid, from start to end of way.
                    insertwaypoint(wayid_for_point, x, pointlist[x])
                    connection.commit()
                pointlist = []

def executenodetag():
    for event, elem in ET.iterparse(inputfile, events=('start', 'end', 'start-ns', 'end-ns')):
        if elem.tag == 'node':
            if elem.tag == 'node' and event == 'start':
                nodeid = elem.attrib['id']
                tagroot = elem
                for elem in tagroot:
                    if elem.tag == 'tag':
                        #print(nodeid, elem.attrib['k'])
                        #extract necessary tag data by iterating through node
                        insertnodetag(nodeid, elem.attrib['k'], elem.attrib['v'])
                        connection.commit()
            elif elem.tag == 'node' and event == 'end' and nodeid == elem.attrib['id']:
                #print("MATCH")
                continue

def executewaytag():
    for event, elem in ET.iterparse(inputfile, events=('start', 'end', 'start-ns', 'end-ns')):
        if elem.tag == 'way':
            if elem.tag == 'way' and event == 'start':
                wayid_for_tag = elem.attrib['id']
                tagroot = elem
                for elem in tagroot:
                    if elem.tag == 'tag':
                        #print(nodeid, elem.attrib['k'])
                        #extract necessary tag data by iterating through node
                        insertwaytag(wayid_for_tag, elem.attrib['k'], elem.attrib['v'])
                        connection.commit()
            elif elem.tag == 'way' and event == 'end' and wayid_for_tag == elem.attrib['id']:
                #print("MATCH")
                continue




def main():


    droptable()
    createtable()
    executenode()
    executeway()
    executewaypoint()
    executenodetag()
    executewaytag()



main()
