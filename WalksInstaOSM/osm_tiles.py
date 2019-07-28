import requests
import math
from PIL import Image, ImageDraw
import os 
import csv
import urllib.parse
import random

class Stats():
    def __init__(self):
        # Read the current stats file
        pass

class Tiles():
    def __init__(self, startPos, endPos, deltas, zoom,filename,main=False):
        # Initialise positional parameters
        self.lat_deg, self.lon_deg = startPos
        self.end_lat, self.end_lon = endPos
        self.delta_lat, self.delta_long = deltas
        self.zoom = zoom
        self.filename = filename
        self.is_main = main
    def deg2num(self, lat_deg, lon_deg, zoom):
      lat_rad = math.radians(lat_deg)
      n = 2.0 ** zoom
      xtile = int((lon_deg + 180.0) / 360.0 * n)
      ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
      return (xtile, ytile)
   
    def deg2num2(self, lat_deg, lon_deg, zoom):
      lat_rad = math.radians(lat_deg)
      n = 2.0 ** zoom
      xtile = int((lon_deg + 180.0) / 360.0 * n)
      x_ = (lon_deg + 180.0) / 360.0 * n - xtile
      ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
      y_ = (1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n - ytile
      return (xtile, ytile,x_,y_)
    
    def num2deg(self, xtile, ytile, zoom):
      n = 2.0 ** zoom
      lon_deg = xtile / n * 360.0 - 180.0
      lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
      lat_deg = math.degrees(lat_rad)
      return (lat_deg, lon_deg)
    
    def getImageCluster(self):
        smurl = r"https://a.tile.openstreetmap.org/{0}/{1}/{2}.png"
        xmin, ymax =self.deg2num(self.lat_deg - self.delta_lat, 
                                 self.lon_deg - self.delta_long, self.zoom)
        xmax, ymin =self.deg2num(self.lat_deg + self.delta_lat, 
                                 self.lon_deg + self.delta_long, self.zoom)
        
        xtile, ytile =self.deg2num(self.lat_deg,self.lon_deg, self.zoom)
        xmin = xtile - 2
        xmax = xtile + 2
        if(self.zoom == 7):
            ymin = ytile - 3
            ymax = ytile + 1
        else:
            ymin = ytile - 2
            ymax = ytile + 2
        
        self.xmin, self.ymax, self.xmax, self.ymin = xmin,ymax,xmax,ymin
        
        # Spoof user-agent
        headers = {
                "Host": "a.tile.openstreetmap.org",
                "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0",
                "Accept": "image/webp,*/*",
                "Accept-Language": "en-GB,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection":"keep-alive",
                "Cache-Control": "max-age=0",
                "TE": "Trailers"
                }
        
#        print(xmin,xmax,ymin,ymax)
    
        Cluster = Image.new('RGB',((xmax-xmin+1)*256-1,(ymax-ymin+1)*256-1) ) 
        for xtile in range(xmin, xmax+1):
            for ytile in range(ymin,  ymax+1):
                try:
                    imgurl=smurl.format(self.zoom, xtile, ytile)
#                    print("Opening: " + imgurl)
                    filepath = "tiles/{}_{}.png".format(xtile,ytile)
                    # Check if tile already exists
                    if(not os.path.isfile(filepath)):
                        # Download the tile
                        response = requests.get(imgurl,headers=headers)
                        if response.status_code == 200:
                            with open(filepath, 'wb') as f:
                                f.write(response.content)
                        else:
                            print("[{}] Can't download tile {}".format(response.status_code,imgurl))
                    else:
                        pass
                    
                    tile = Image.open(filepath)
                    #print(xtile)
                    Cluster.paste(tile, box=((xtile-xmin)*256 ,  (ytile-ymin)*255))
                except: 
                    print("Couldn't download image")
                    tile = None
    
        return Cluster

    def pixel2longlat(self, pos):
        # Extract pixels
        x,y = pos
        xtile,ytile = self.xmin + x/256, self.ymin + y/256
        
        return (self.num2deg(xtile,ytile,self.zoom))
    
    def longlat2pixel(self, pos):
        """ 
        run this function to return pixel coordinate of some degree position
        """
        # Coordinate of the point
        lat, long = pos
        
        n = self.deg2num2(lat,long,self.zoom)
        x = 256 * (n[0] - self.xmin) + n[2]*256
        y = 256 * (n[1] - self.ymin) + n[3]*256
        
        return (x,y)
        
    def addPoints2map(self, mapname, points, param = None):
        """
        Function to add points to the map
        """
        # Open output image
        img = Image.open(self.filename)
#        print(points,mapname)
        draw = ImageDraw.Draw(img)
        for i in range(len(points)):
            point = points[i]
            x,y = self.longlat2pixel([float(point[0]),float(point[1])])
#            print(x,y)
            if(i == len(points) -1 ):
                if(param == 1):
                    draw.line((x-30,y-30) + (x+30,y+30), width=10, fill = (255,0,255))
                    draw.line((x-30,y+30) + (x+30,y-30), width=10, fill = (255,0,255))
                else:
                    draw.line((x,y) + (x,y+5), width=10, fill = (0,0,255))
                #draw.line((x,y+100)+(x2+100,y2), width=10, fill=(255,0,255))
            else:
                point2 = points[i+1]
                x2,y2 = self.longlat2pixel([float(point2[0]),float(point2[1])])
                draw.line((x,y)+(x2,y2), width=5, fill=(255,50,200))
        #draw.line(self.longlat2pixel((51.3821, -2.3578+0.001)) + self.longlat2pixel((51.3821, -2.3578)), width=5, fill=(0,0,255,100))
        img.save(mapname)
        
    def draw_destination_direction(self):
        """
        Function to draw end point on the map
        """
        
        # Open output image
        img = Image.open(self.filename)
        draw = ImageDraw.Draw(img)
        
        # Check whether end point is visible on the map
        if(self.end_lat > self.lat_deg - self.delta_lat and 
           self.end_lat < self.lat_deg + self.delta_lat):
            # Visible
            # Highlight that point on the map
            x,y = self.longlat2pixel((self.end_lat,self.end_lon))
#            print(x,y)
            draw.ellipse((x-20,y-20,x+20,y+20),width = 10, outline = (255,74,90))
        else:
            # Not visible
            # Draw an arrow towards the destination
            pass
        img.save(self.filename)
        
    def drawPointOnMap(self,point):
        """
        Function to draw a point on the map given a long-lat
        """
        img = Image.open(self.filename)
        lat,lon = self.lat_deg, self.lon_deg
        lat,lon = (51.3805, -2.3448)
        n = self.deg2num2(lat,lon,self.zoom)
        x_,y_ = n[2]*256, n[3]*256
        x = 256 * (n[0] - self.xmin) + n[2]*256
        y = 256 * (n[1] - self.ymin) + n[3]*256
        draw = ImageDraw.Draw(img)
        draw.line((x,y)+(x+1,y),width=10,fill=(0,0,0))
        
    def updateHistoricFile(self, steps):
        # Update historic travels file
        with open("history.csv", "r") as f:
            reader = csv.reader(f)
            hist = list(reader)
#        if(len(hist) > 2000):
#            new_list = hist[len(hist)-1000:]
#            with open("history.csv","w") as f:
#                writer = csv.writer(f, lineterminator="\n")
#                writer.writerows(new_list)
        with open("history.csv", "a") as output:
            writer = csv.writer(output, lineterminator='\n')
            writer.writerows(steps)
        
    def osm_directions(self,max_dist):
        """
        Use OSM to find directions all the way to the end point
        Otherwise I get lost lol
        """
        start = (self.lat_deg, self.lon_deg)
        end = (self.end_lat, self.end_lon)
        url = "https://routing.openstreetmap.de/routed-foot/route/v1/driving/{0},{1};{2},{3}?overview=false&geometries=polyline&steps=true"
        url = url.format(start[1],start[0],end[1],end[0])
        r = requests.get(url)
        r = r.json()
        routes = r["routes"]
        steps = routes[0]["legs"][0]["steps"]
        # Go through the given JSON and extract location of each turn
        locs = []  # List of locations
        dist_tmp = 0
        dur_tmp = 0
        total_dist = routes[0]["distance"]
#        print(len(steps))
        for step in steps:
#            print(step)
            dist = step["distance"]
            dur = step["duration"]
            locs.append([step["maneuver"]["location"][1],step["maneuver"]["location"][0]])
            for inter in step["intersections"]:
                locs.append([inter["location"][1],inter["location"][0]])
                pass
            dist_tmp += dist
            dur_tmp += dur
            #print(dist_tmp,max_dist)
            locs_ = [x for i, x in enumerate(locs) if locs.index(x) == i]
            if(dist_tmp > max_dist and len(locs_) > 1):
#                print(step["distance"])
                break
#        print(start,end)
#        print(locs)
        return [locs,[dist_tmp,total_dist],dur]
            
    def updateMap(self):
        # Read historic file
        with open('history.csv', 'r') as f:
          reader = csv.reader(f)
          history = list(reader)
        # Find current end point
        #endpoint_c = self.findEndPoint()
        # Use OSM navigation to find the end point
        max_travel_dist = 1000  # How far to check the map in this step
        dirs = self.osm_directions(max_travel_dist)  # List of directions with stats
        # Destination deg
        pos_d = dirs[0][-1]
        # Current position deg
        pos_c = self.lat_deg,self.lon_deg
#        print(dirs[0])
        # Find directions between current and end point
        #steps = self.retrieveDirectrions(pos_c,pos_d)
        # Plot the points on the map
        self.addPoints2map(self.filename,dirs[0],0)
        # Plot historic travel in different colour
        self.addPoints2map(self.filename,history)
        if(self.is_main):
            # Append the historic file
            self.updateHistoricFile(dirs[0])       
        # Annotate end goal on the map
        self.draw_destination_direction()
        # Add other fun stats 
        #   (distance traveled, distance to destination, destination name
        #       time taken so far, current time, time to destination)
        # 2 zoomed out views to show where I'm going and where I've been
    
    def resize(self):
        img = Image.open(self.filename)
        img = img.resize((1080,1350))
        img.save(self.filename)
        
class Traveller():
    def find_town_from_postcode(self,postcode):
        """
        This website will give me the town name from the postcode
        """
        # Extract the main part of the postcode
        url = "https://www.doogal.co.uk/UKPostcodes.php?Search={}"
        url = url.format(urllib.parse.quote(postcode))
        r = requests.get(url)
        if(r.status_code == 200):
#            print(url)
            text = r.text
            i = text.index("<small>")
            j = text.index("</small>",i)
            name = (text[i + len("<small>"):j])
            return name
        else:
            return ""
        
        
    def find_next_destination(self):
        """
        Function to pick a random postcode within the UK to travel to
        Luckily website I found also returns lat and long
        """
        url = "https://www.doogal.co.uk/CreateRandomPostcode.ashx"
        r = requests.get(url)
        if(r.status_code == 200):
            html = str(r.content).replace("\\n","").replace("b'","").replace("'","")
            return_list = html.split(",")
#            print(return_list)
            for i in range(1,3):
                return_list[i] = eval(return_list[i])
            name = self.find_town_from_postcode(return_list[0])
            return_list.append(name)
            return return_list
        else:
            rnd_dests = [ ["",51.3778,-2.3253,"Bath University"], 
                          ["",51.4769,0,"Greenwich"],
                          ["",52.0572,1.2253,"Ipswich"]]
            i = random.randint(0,len(rnd_dests)-1)
            return rnd_dests[i]
        
    def __init__(self):
        # Read historic file
        with open('history.csv', 'r') as f:
          reader = csv.reader(f)
          history = list(reader)
        # Read destinations file
        with open("destinations.csv","r") as f:
            reader = csv.reader(f)
            dest = list(reader)
#        print(history[-1])
                
        startPos = (float(history[-1][0]),float(history[-1][1]))
        endPos = (float(dest[0][1]),float(dest[0][2]))
        
        # Check if destination had been reached        
        dist_between = math.sqrt( (startPos[0]-endPos[0])**2
                                 +(startPos[1]-endPos[1])**2)
        if(dist_between < 0.005):
            # Destination had been reached
            next_pos = self.find_next_destination()
            endPos = (next_pos[1],next_pos[2])
            dest.insert(0,next_pos)
            # Add new destination to the file
            with open("destinations.csv", "w") as output:
                writer = csv.writer(output, lineterminator='\n')
                writer.writerows(dest)
        else:
            pass
        
        deltas = (2, 2)
        zoom = 14
        
        filename = "o.png"
#        print(startPos, endPos, zoom)
        t = Tiles(startPos, endPos, deltas, zoom,filename,main=True)
    
        a = t.getImageCluster()
        a.save(filename)
        t.updateMap()
        t.resize()
        print("Done 1")
        deltas = (2,2)
        zoom = 12
        
        filename = "o2.png"
        t = Tiles(startPos, endPos, deltas, zoom,filename)
    
        a = t.getImageCluster()
        a.save(filename)
        t.updateMap()
        t.resize()
        print("Done 2")
        
        deltas = (2,2)
        zoom = 7
        
        filename = "o3.png"
        t = Tiles(startPos, endPos, deltas, zoom,filename)
    
        a = t.getImageCluster()
        a.save(filename)
        t.updateMap()
        t.resize()
        print("Done 3")

        

if __name__ == '__main__':
    travel = Traveller()