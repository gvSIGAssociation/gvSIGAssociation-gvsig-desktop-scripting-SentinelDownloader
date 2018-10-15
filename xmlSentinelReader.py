# encoding: utf-8

import gvsig

import pprint, os, urllib2, base64

from gvsig import geom
from gvsig.libs.formpanel import FormPanel

from java.io import File
from java.lang import Object
from javax.imageio import ImageIO
from javax.swing.tree import TreeCellRenderer
from javax.swing import SpinnerNumberModel, DefaultListModel, ImageIcon,JLabel, ListCellRenderer, BorderFactory, JSpinner
from java.awt import Color

from xml.etree import ElementTree as ET

from java.awt import Image
from java.awt.image import BufferedImage
import threading
from sentinelDownloadManager import SentinelDownloadManager

def download(url):
    username=""
    password=""
    request = urllib2.Request(url)
    base64string = base64.b64encode('%s:%s' % (username, password))
    request.add_header("Authorization", "Basic %s" % base64string)
    result = urllib2.urlopen(request)
    return result
    
def downloadXMLQuery(url):
    #try:
    outputPath=gvsig.getTempFile("sentinelXML", ".xml")
    f = download(url)
    #total_size = int(f.headers["Content-Length"])
    #MB_size = round(total_size/1048576, 2)
    block_size = 1024 * 1024
    with open(outputPath, "wb") as file:
      while True:
        block = f.read(block_size)
        dSize =  round(int(os.stat(outputPath).st_size)/1048576, 2)
        #print "(" + str(dSize) + "/" + str(MB_size) + " MB) " +  url + "Downloading"
        if not block:
          break
        file.write(block)
    return outputPath
    #except:
    #  return None
    
class SentinelProduct(Object):
  def __init__(self,name,info):
    self.name = name
    self.info = info
  def getName(self):
    return self.name
  def getInfoString(self):
    pp = pprint.PrettyPrinter(indent=1)
    x = pp.pformat(self.info)
    return x
  def toString(self):
    return str(self.name)
  def getPreviewLink(self):
    return self.info["link_icon"]
  def getDownloadLink(self):
    return self.info["link"]
    
def createSentinelQuery(start, rows, params, sortbyParam):
   ## Generate params
    queryParams=""
    count = 0
    for k in params.keys():
      value = params[k]
      if value==None or value=="" or value=="---":
        continue
      if count!=0:
        queryParams+=" AND "

      queryParams+="{0}:{1}".format(k,params[k])
      count+=1
    ##
    sortby="orderby=%s"%(sortbyParam)
    finalQuery = "https://scihub.copernicus.eu/dhus/search?start={0}&rows={1}&q=({2})&{3}".format(start,rows,queryParams,sortby)
    return finalQuery


    
class SentinelSearchPanel(FormPanel):
  def __init__(self):
    FormPanel.__init__(self,gvsig.getResource(__file__, "sentinelSearchPanel.xml"))
    #self.setPreferredSize(300,700)
    self.params = None
    self.mapControl = None
    self.start=0
    self.rows=10
    self.sortby="ingestiondate%20asc"
    # Init components
    self.lblPreview.setBorder(BorderFactory.createEmptyBorder())
    platformOptions = ["---", "Sentinel-1", "Sentinel-2", "Sentinel-3"]
    for k in platformOptions: self.cmbPlatform.addItem(k)
    polarisation = ["---","HH", "VV", "HV", "VH", "HH HV", "VV VH"]
    for k in polarisation: self.cmbPolarisation.addItem(k)
    sensors = ["---","SM", "IW", "EW", "WV"]
    for k in sensors: self.cmbSensor.addItem(k)
    model1 = SpinnerNumberModel(5.0, 0.0, 100.0, 1.0);  
    #spin1 = JSpinner(model1)
    self.spnCloud.setModel(model1)
    self.txtInfo.setCaretPosition(0)
    ## Download manager
    self.downloadManager = SentinelDownloadManager(self)
  def setToolMapControl(self, mapControl):
    self.mapControl = mapControl
    
  def getDownloadManager(self):
    return self.downloadManager
    
  def btnStop_click(self, *args):
    self.getDownloadManager().setStopThread(True)
    
  def setProducts(self, products):
    m = DefaultListModel()
    for k in products.keys():
      product = SentinelProduct(k,products[k])
      m.addElement(product)
    self.lstProducts.setModel(m)
    
  def btnDownload_click(self, *args):
    value = self.lstProducts.getSelectedValue()
    name = value.getName()
    sentinelUrl = value.getDownloadLink()
    dm = self.getDownloadManager()
    dm.addDownload(name, sentinelUrl)

  def btnNext_click(self,*args):
    self.start+=10
    threading.Thread(target=self.startSearch, name="SearchSentinel", args=(True,)).start()
    
  def btnPrevious_click(self,*args):
    if self.start<=self.rows:
      self.start=0
    else:
      self.start-=10
    threading.Thread(target=self.startSearch, name="SearchSentinel", args=(True,)).start()
    
    
  def btnSearch_click(self, *args):
    threading.Thread(target=self.startSearch, name="SearchSentinel", args=()).start()
    
  def startSearch(self,repeat=False):
    self.txtStatus.setText("Searching..")
    self.setProducts({})
    self.lblPreview.setIcon(None)
    self.txtInfo.setText("")
    if repeat==False:
      if not self.chbUseQuery.isSelected():
        #print "txtMyQuery", self.txtMyQuery.getText(), type(self.txtMyQuery.getText())
        self.params = {}
        filename=self.txtFilename.getText()
    
        self.params["filename"]=filename
        self.params["platformname"]=self.cmbPlatform.getSelectedItem()
        self.params["polarisationmode"]=self.cmbPolarisation.getSelectedItem()
        self.params["sensoroperationalmode"]=self.cmbSensor.getSelectedItem()
        if self.spnCloud.getValue()==100:
          v = None
        else:
          v = self.spnCloud.getValue()
        self.params["cloudcoverpercentage"]=v
        self.start=0
        self.rows=10
        self.lblResultsNumber.setText(str(self.start)+" / "+str(self.rows))
        finalQuery = createSentinelQuery(self.start, self.rows, self.params, self.sortby)
        #self.txtQuery.setText(finalQuery)
      else:
        finalQuery = self.txtMyQuery.getText()
      
    else: #repeat true
      finalQuery = createSentinelQuery(self.start, self.rows, self.params, self.sortby)
    finalQuery = finalQuery.replace(" ","%20")
    print finalQuery
    try:
      xmlPath = downloadXMLQuery(finalQuery)
      products = xmlSentinelReader(xmlPath)
      self.setProducts(products)
    except:
      self.txtStatus.setText("Bad request: "+finalQuery)
    #UI update
    self.lblResultsNumber.setText(str(self.start)+" / "+str(self.start+self.rows))
    self.txtStatus.setText("Done!")
    
  def lstProducts_change(self, *args):
    threading.Thread(target=self.updateProduct, name="UpdateProductSentinel", args=(True,)).start()
    
  def updateProduct(self, *args):
    try:
      value = self.lstProducts.getSelectedValue()
    except:
      return
    if value==None:
      return
    #try:
    if True:
      width=150
      height=150
      #gvSIGPath = Utilities.TEMPDIRECTORYPATH
      gvSIGPath = "/home/osc/temp"
      outputPath=os.path.join(gvSIGPath,value.getName()+"_%sx%s.jpg"%(width,height)) #Utilities.TEMPDIRECTORYPATH

      if os.path.exists(outputPath)==False:
        url = value.getPreviewLink()
        f = download(url)
        total_size = int(f.headers["Content-Length"])
        MB_size = round(total_size/1048576, 2)
        block_size = 1024 * 1024
        outputPathFull=gvSIGPath+value.getName()+".jpg"
        with open(outputPath, "wb") as file:
          while True:
            block = f.read(block_size)
            dSize =  round(int(os.stat(outputPath).st_size)/1048576, 2)
            print "(" + str(dSize) + "/" + str(MB_size) + " MB) " +  url + "Downloading"
            if not block:
              break
            file.write(block)
        img = ImageIO.read(outputPathFull)
        tmp = img.getScaledInstance(width, height, Image.SCALE_SMOOTH)
        resized = BufferedImage(width, height, BufferedImage.TYPE_INT_ARGB)
        g2d = resized.createGraphics()
        g2d.drawImage(tmp, 0, 0, None)
        g2d.dispose()
        ImageIO.write(resized, "jpg", outputPath)
      else:
        print "already downloaded"
      myPicture = ImageIcon(ImageIO.read(File(outputPath)))
      self.txtInfo.setText(value.getInfoString())
      self.tabInfo.updateUI()
      self.lstProducts.updateUI()
      self.lstProducts.revalidate()
      self.lstProducts.repaint()
    #except:
    #  myPicture = ImageIcon()
    self.lblPreview.setIcon(myPicture)

def main(*args):
  l = SentinelSearchPanel()
  l.showTool("SentinelSearchPanel")
  xml = gvsig.getResource(__file__,"test","sentinelSearch1.xml")
  #p = xmlSentinelReader(xml)
  #l.setProducts(p)
  #print p
  
  
def xmlSentinelReader(xml):
  tree = ET.parse(xml)
  root = tree.getroot()
  products = {}
  for child in root:
    #print "TAG:", child.tag#, child.attrib
    ### ENTRY
    childInfo = {}
    if child.tag=="{http://www.w3.org/2005/Atom}entry":
      for c in child:
        #print c.tag, c.attrib, c.text
        if c.tag=="{http://www.w3.org/2005/Atom}link":
          if "rel" in c.attrib:
              childInfo["link_"+c.attrib["rel"]]=c.attrib["href"]
          else:
              childInfo["link"]=c.attrib["href"]
              
        if c.tag=="{http://www.w3.org/2005/Atom}title":
          idProduct = c.text
          childInfo[c.get("name")]= c.text
        if c.get("name")!=None:
          if c.tag=="{http://www.w3.org/2005/Atom}int":
            childInfo[c.get("name")]=int(c.text)
          else:
            childInfo[c.get("name")]=c.text

      products[idProduct]=childInfo

  #pp = pprint.PrettyPrinter(indent=1)
  #pp.pprint(products)
  return products