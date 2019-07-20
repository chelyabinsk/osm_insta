import requests
import math
from PIL import Image, ImageDraw
import os 
import json

class Tiles():
    def __init__(self, startPos, endPos, deltas, zoom):
        # Initialise positional parameters
        self.lat_deg, self.lon_deg = startPos
        self.end_lat, self.end_lon = endPos
        self.delta_lat, self.delta_long = deltas
        self.zoom = zoom
        
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
    
        Cluster = Image.new('RGB',((xmax-xmin+1)*256-1,(ymax-ymin+1)*256-1) ) 
        for xtile in range(xmin, xmax+1):
            for ytile in range(ymin,  ymax+1):
                try:
                    imgurl=smurl.format(zoom, xtile, ytile)
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
        img = Image.open("o4.png")
        draw = ImageDraw.Draw(img)
        for i in range(len(points)):
            point = points[i]
            x,y = self.longlat2pixel([point[1],point[0]])
            if(i == len(points) -1 ):
                draw.line((x,y) + (x+1,y), width=5, fill = (0,0,255))
            else:
                point2 = points[i+1]
                x2,y2 = self.longlat2pixel([point2[1],point2[0]])
                draw.line((x,y)+(x2,y2), width=5, fill=(0,0,255))
        #draw.line(self.longlat2pixel((51.3821, -2.3578+0.001)) + self.longlat2pixel((51.3821, -2.3578)), width=5, fill=(0,0,255,100))
        img.save(mapname)
    
    def retrieveDirectrions(self, start, end):
        """
        Use this function to figure out directions between two points
        on the map. I am going to use it to fill in the gaps in my travels
        All credit goes to the OSM directions.
        """
        url = "https://routing.openstreetmap.de/routed-foot/route/v1/driving/{0},{1};{2},{3}?overview=false&geometries=polyline&steps=true"
        url = url.format(start[1],start[0],end[1],end[0])
        r = requests.get(url).json()
        routes = r["routes"]
        dist = routes[0]["distance"]
        dur = routes[0]["duration"]
        steps = routes[0]["legs"][0]["steps"]
        # Go through the given JSON and extract location of each turn
        locs = []  # List of locations
        for step in steps:
            for inter in step["intersections"]:
                locs.append(inter["location"])
            locs.append(step["maneuver"]["location"])
        return locs
        
        #https://routing.openstreetmap.de/routed-foot/route/v1/driving/-2.3648278,51.3838674;-2.3626613616943364,51.386499401860114?overview=false&geometries=polyline&steps=true
        #https://routing.openstreetmap.de/routed-foot/route/v1/driving/-2.3647764572097345,51.38379438500331;-2.3548,51.3812?overview=false&geometries=polyline&steps=true
        #https://routing.openstreetmap.de/routed-foot/route/v1/driving/51.38379438500331,-2.3647764572097345;51.3812,-2.3548?overview=false&geometries=polyline&steps=true
    def findEndPoint(self):
        """
        Function to find valid end step
        
        Function wil bias towards the end goal. End point can only be placed 
        on pedestrian friendly roards. Minimum radius is 0.005 of a degree
        since updates are going to be around every 15 minutes
        
        Gonna use polar coordinate just cos it's easier to draw circles
        """
        # Find current position coordinate
        c_x, c_y = self.longlat2pixel((self.lat_deg,self.lon_deg))
        # Find end position coordinate)
        f_x, f_y = self.longlat2pixel((self.end_lat, self.end_lon))
        # Find relative angle between two points
        theta = math.pi + math.acos((c_x-f_x)/math.sqrt((c_x-f_x)**2 + (c_y-f_y)**2.0))
        # Define starting searching radius
        r_ = 0.005  # ~1km
        # Define initial number of points on the circle
        n = 5000.0
        
        img = Image.open("o.png")
        rgb_img = img.convert("RGB")
        r_x_, r_y_ = self.longlat2pixel((0,0))
        r_x, r_y = self.longlat2pixel((r_,r_))
        r_x, r_y = abs(r_x_ - r_x), abs(r_x_ - r_x)
#        print(r_x,r_y)
#        print(theta)
        
        # Two cases, end point is outside the search radius
        #   travel in the naive direction
        # End point is withint the search radius,
        #   simply look for end point
        
        # Find distance between current and end points
        dist = math.sqrt(((c_x - f_x) ** 2 + (c_y - f_y)**2))
        
        # If end point is outside of the search radius
        if(dist > r_x):
            for i in range(int(n/2)):
                x = c_x + r_x*math.cos(theta + (i/n)*math.pi*2 * (-1)**i)
                y = c_y + r_y*math.sin(theta + (i/n)*math.pi*2 * (-1)**i)
                # Extract pixel's RGB components
                r,g,b = rgb_img.getpixel((x,y))
#                r,g,b = (0,0,0)
                # Yellow A-road
                drawDot = False
                if(r == 252 and g== 214 and b == 164):
                    drawDot = True
                # White town street                
                elif(r == 255 and g == 255 and b == 254):
                    drawDot = True
                elif(r == 255 and g == 255 and b == 255):
                    drawDot = True
                elif(r == 254 and g == 255 and b == 254):
                    drawDot = True
                elif(r == 255 and g == 254 and b == 254):
                    drawDot = True
                elif(r == 254 and g == 254 and b == 254):
                    drawDot = True
                # Less yellow public road
                elif(r == 247 and g == 248 and b == 189):
                    drawDot = True
                # Pink A-road
                elif(r == 249 and g == 178 and b == 156):
                    drawDot = True
#                drawDot  = True
                if(drawDot):
                    break
    #                print(x,y)
        else:
            x,y = f_x, f_y
        draw = ImageDraw.Draw(img)    
#        draw.line((x,y)+(x+10,y+10),width=5,fill=(255,0,0,0))
        
#        draw.line((c_x,c_y)+(c_x,c_y+5),width=20,fill=(0,0,255,0))
#        draw.line((f_x,f_y)+(f_x,f_y+5),width=20,fill=(0,0,255,0))
        img.save("o4.png")
        return (x,y)
    
    def drawPointOnMap(self,point):
        """
        Function to draw a point on the map given a long-lat
        """
        img = Image.open("o.png")
        lat,lon = self.lat_deg, self.lon_deg
        lat,lon = (51.3805, -2.3448)
        n = self.deg2num2(lat,lon,self.zoom)
        x_,y_ = n[2]*256, n[3]*256
        x = 256 * (n[0] - self.xmin) + n[2]*256
        y = 256 * (n[1] - self.ymin) + n[3]*256
        draw = ImageDraw.Draw(img)
        draw.line((x,y)+(x+1,y),width=10,fill=(0,0,0))
#        img.save("o3.png")
#        print(lat,lon,x,y)
#        print(self.xmin,self.xmax,n)
        
    def updateMap(self):
        # Find current end point
        endpoint_c = self.findEndPoint()
        # Destination deg
        pos_d = self.pixel2longlat(endpoint_c)
        # Current position deg
        pos_c = self.lat_deg,self.lon_deg
#        print(pos_d,pos_c)
        # Find directions between current and end point
        steps = self.retrieveDirectrions(pos_c,pos_d)
        # Plot the points on the map
        self.addPoints2map("o4.png",steps)
        # Plot historic travel in different colour
        
        # Add other fun stats
        

if __name__ == '__main__':
    startPos = (51.3812, -2.3548)
    endPos = (51.3704,-2.3184)
    deltas = (0.01, 0.02)
#    deltas = (0.001, 0.005)
    zoom = 15
    
    t = Tiles(startPos, endPos, deltas, zoom)

    a = t.getImageCluster()
#    fig = plt.figure()
#    fig.patch.set_facecolor('white')    
#    plt.imshow(np.asarray(a))
#    plt.show()
    a.save("o.png")
    b = a.resize((1080,1080),Image.ANTIALIAS)
#    b.save("o2.png")
    #t.addPoints2map(1,1,1)
    t.updateMap()
#    print(t.longlat2pixel((51.3812,-2.3548)))