import requests
import math
from PIL import Image, ImageDraw
import os 

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
                    print("Opening: " + imgurl)
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
        lat = (2.0*self.delta_lat/1080.0)*(x)+self.lat_deg - self.delta_lat
        lon = (2.0*self.delta_long/1080.0)*(y)+self.lon_deg - self.delta_long
        return (lat,lon)
    
    def longlat2pixel(self, pos):
        """ 
        run this function to return pixel coordinate of some degree position
        """
        # Coordinate of the point
        lat, long = pos
        # Image size is fixed to 1080x1080
        w, h = (1279, 1023)
        # Find corner degrees
        lat_min,lon_min = self.num2deg(self.xmin,self.ymin,self.zoom)
        lat_max,lon_max = self.num2deg(self.xmax,self.ymax,self.zoom)
        lon_max += self.delta_long*1.4
        lat_max -= self.delta_lat*0.04
#        print(lat_min,lon_min,lat_max,lon_max)
        x = (w/(lat_max-lat_min)*1.0)*(lat - (lat_min))
#        y = (h/h_d)*(long - (self.lon_deg-self.delta_long))
        y = (h/(lon_max-lon_min)*1.0)*(long - (lon_min))
        return (x,y)
        
    def addPoints2map(self, mapname, points, param = None):
        """
        Function to add points to the map
        """
        # Open output image
        img = Image.open("o.png")
        draw = ImageDraw.Draw(img)
        draw.line(self.longlat2pixel((51.3821, -2.3578+0.001)) + self.longlat2pixel((51.3821, -2.3578)), width=5, fill=(0,0,255,100))
        img.save("o3.png")
    
    def findEndPoint(self):
        """
        Function to find valid end step
        
        Function wil bias towards the end goal. End point can only be placed 
        on pedestrian friendly roards. Minimum radius is 0.001 of a degree
        since updates are going to be around every 15 minutes
        
        Gonna use polar coordinate just cos it's easier to draw circles
        """
        # Find current position coordinate
        c_x, c_y = self.longlat2pixel((self.lat_deg,self.lon_deg))
        # Find end position coordinate
        f_x, f_y = self.longlat2pixel((self.end_lat, self.end_lon))
        # Find relative angle between two points
        theta = math.asin((c_x-f_x)/math.sqrt((c_x-f_x)**2 + (c_y-f_y)**2.0))
        # Define starting searching radius
        r = 0.005  # ~1km
        # Define initial number of point on the circle
        n = 100.0
        
        img = Image.open("o.png")
        r_x_, r_y_ = self.longlat2pixel((0,0))
        r_x, r_y = self.longlat2pixel((r,r))
        r_x, r_y = abs(r_x_ - r_x), abs(r_x_ - r_x)
        print(r_x,r_y)
        for i in range(int(n)):
            draw = ImageDraw.Draw(img)
            x = c_x + r_x*math.cos(theta + i/n*math.pi*2)
            y = c_y + r_y*math.sin(theta + i/n*math.pi*2)
            draw.line((x,y)+(x+10,y+10),width=10,fill=(255,0,0,0))
        draw.line((c_x,c_y)+(c_x,c_y+5),width=20,fill=(0,0,255,0))
        draw.line((f_x,f_y)+(f_x,f_y+5),width=20,fill=(0,0,255,0))
        img.save("o4.png")

if __name__ == '__main__':
    startPos = (51.3812, -2.3548)
    endPos = (51.3875, -2.3550)
    deltas = (0.01, 0.02)
    zoom = 15
    t = Tiles(startPos, endPos, deltas, zoom)

    a = t.getImageCluster()
#    fig = plt.figure()
#    fig.patch.set_facecolor('white')    
#    plt.imshow(np.asarray(a))
#    plt.show()
    a.save("o.png")
    b = a.resize((1080,1080),Image.ANTIALIAS)
    b.save("o2.png")
    #t.addPoints2map(1,1,1)
    t.findEndPoint()
#    print(t.longlat2pixel((51.3812,-2.3548)))