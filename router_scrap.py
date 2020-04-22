import sys
import argparse
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from datetime import date
from datetime import datetime as dt
from calendar import monthrange
from time import sleep

#
# Installation steps:
#
#   0. Install python3 on your target system
#   1. Install selenium:    # pip3 install selenium (Python3!!)
#   2. Download driver for firefox (geckodriver) or chrome (chromedriver)
#   3. For Firefox, driver is only one geckodriver.exe file, which should be installed 
#      in a PATH honored folder.
#   4. Developpers hint: For fast prototyping, install SELENIUM IDE in Firefox or Chrome (add-on)
#       record a test with mouse & Clicks and export it as python webdriver. 
#

cfg_browser = 'Firefox'     # Default browser for webdriver.   Use = 'Chrome' for Google browser
user='1234'                 # Username for login into router
mykey='jeccam69'            # passwd for longin into router
maclist =[]                 # MAC Adress list for removing MACs
maclist2=[]                 # MAC Adress list for adding   MACs
set_mode=''                 # MAC table Mode to be set (opt_set = True)
jobs = 0                    # Set to True if something to do

#
# Command line options helpers
#

opt_dev_name = ''       # target router name
opt_debug = ''          # Debug mode 
opt_add = ''            # option add MACs
opt_rm = ''             # option remove MACs
opt_ls = ''             # option list MACs
opt_set = ''            # option set MAC table mode

#
# ZTE F680 - Custom Settings
# 
#    TO DO: add all F680 constants here
#
mac_modes = ('Block','Disabled','Permit')


class WifiRouter:
    '''class WifiRouter stores all the information and methods to scrap a hw_model's web pages
            hw_model attribute stores hw_models name, and should be used to drive/fork different
             hw_model's web pages, probably indexing a scrap_steps dictionary'''


    def __init__(self, name, homepage):

        self.macs24_list = []   # List ofcurrent MAC adresses in ACL table for 2.4GHz wifi
        self.hw_model = name
        self.site = homepage
        self.elem = None
        self.elems = None
        self.cur_menu = None    # set to last menu option clicked / selected
        self.logged_in = False  # Router session status

    #
    # add_acl : adds and Access Control List (ACL) 
    #

    def add_acl(self, macs):

        self.acl_macs = []      # device MAC Address as 12 characters string

        if self.hw_model == masmovil1:

            for item in macs :

                self.acl_macs.append(item.lower())     # device MAC Address as 12 characters string lowercased for ZTE F680

            if opt_debug :
                print("router.add_acl(): about to add following MACs: ",self.acl_macs)

            self.goto_menu("Network-WLAN Radio2.4G(Online)-Access Control List")

            for m in self.acl_macs :
                
                # click | id=mac1
                self.browser.find_element(By.ID, "mac1").click()

                for pos in range(0,11,2) :
                   
                    # type | id=mac1..6
                    self.browser.find_element(By.ID, "mac"+str(int(pos/2+1))).send_keys(m[pos:pos+2])

                    # click | id=add 
                    self.browser.find_element(By.ID, "add").click()

                sleep(20)       # wait some time for router cfg reSync

    def find_element(self, Bytype, descrp, uniq):

        self.elem_type=Bytype
        self.elem_name=descrp

        del self.elem

        #
        # Find web page element(s) / stored in self.elem
        #
        #self.wait_for(self.elem_type,self.elem_name)

        try:
            if uniq:
                qty = 'element'
                self.elem = self.browser.find_element(self.elem_type,self.elem_name)

            else:
                qty = 'elements'
                self.elem = self.browser.find_elements(self.elem_type, self.elem_name)

            if self.elem.size['height'] == 0.0 and self.elem.size['width'] == 0.0 :
                return False

            return True

        except:
                print('Warning in class '+self.__class__.__name__ + ' :  Was not able to find '+ qty +' ['+ descrp + '] By=',self.elem_type)
                return False


    #
    # get_table_column : Scrapt a full column from an HTML table 
    #

    def get_table_column(self, table_id, column_id):

        self.macs24_list = []

        table =  self.browser.find_element(By.ID, table_id)

        table_tags = [ item for item in table.find_elements_by_class_name("uiNoBorder") ]

        for table_tag in table_tags:

            if column_id in table_tag.get_attribute("id") :     # check for MACAdress in id attribute

                self.macs24_list.append(table_tag.get_attribute("value").replace(":",""))



    #
    # goto_menu : select menu option 
    #

    def goto_menu(self, menu_name):

        # TO DO: honor router model /hw type

        self.menu = menu_name   # Target _menu option to be selected
                                
        if self.cur_menu == "Main": 

                # 7 | selectFrame | index=1 | 
                self.browser.switch_to.frame(1)
        
                # 8 | click | css=#mmNet > .menuPlusSymbol | 
                self.browser.find_element(By.CSS_SELECTOR, "#mmNet > .menuPlusSymbol").click()
                self.cur_menu = "Network-WLAN Common Setting-WPS PBC"

        if self.cur_menu == "Network-WLAN Common Setting-WPS PBC": 

            # 9 | click | id=smWLANONE | 
            self.browser.find_element(By.ID, "smWLANONE").click()
            self.cur_menu = "Network-WLAN Radio2.4G(Online)-Basic"

        if self.cur_menu == "Network-WLAN Radio2.4G(Online)-Basic": 

            # 10 | click | id=ssmMacFilter1 | 
            self.browser.find_element(By.ID, "ssmMacFilter1").click()
            self.cur_menu = "Network-WLAN Radio2.4G(Online)-Access Control List"

    

    def login(self, user, passw):

        try:
            if cfg_browser == 'Firefox':
                self.browser = webdriver.Firefox()

            elif cfg_browser == 'Chrome':
                self.browser = webdriver.Chrome()

        except:
            print('Was not able to start webdriver browser =>' + cfg_browser)


        if self.hw_model == masmovil1:

            #
            # Set implicit Selenium WebDriver delay
            #
            self.browser.implicitly_wait(10) # seconds

            try:
                self.browser.get(self.site)

            except:
                print('ERROR in class ' + self.__class__.__name__ + ' :  Was not able to open target homepage [' + self.site + ']')
                sys.exit(2)

      
            # click | id=Frm_Username | 
            self.browser.find_element(By.ID, "Frm_Username").click()

            # type | id=Frm_Username
            self.browser.find_element(By.ID, "Frm_Username").send_keys(user)

            # type | id=Frm_Password 
            self.browser.find_element(By.ID, "Frm_Password").send_keys(mykey)

            # sendKeys | id=Frm_Password | ${KEY_ENTER}
            self.browser.find_element(By.ID, "Frm_Password").send_keys(Keys.ENTER)

            # Wait for Menu Frame Load
            self.find_element(By.ID, "mainFrame", True)  # Accounts menu option
            self.cur_menu   = 'Main'
            self.logged_in  = True

    def logout(self):

        if not self.logged_in :
            
            print("logout(): Session not yet open!")
            return

        if self.hw_model == masmovil1:

            #self.browser.switch_to.frame(1)
            self.browser.find_element(By.LINK_TEXT, "Logout").click()

    def quit(self):         # Quits Webdriver session, closing open browser

        if self.logged_in :
            self.logout()   # close router web  session

        if opt_debug :
            print("Ending Webdriver session...")

        self.browser.quit()
            
        
    def rm_acl(self, macs):

        self.acl_macs = []
    
        if self.hw_model == masmovil1:

            # future:  support por 5GHz ACLs

            for item in macs :

                self.acl_macs.append(item.lower())     # device MAC Address as 12 characters string lowercased for ZTE F680


            if opt_debug :
                print("router.rm_acl(): about to remove following MACs: ",self.acl_macs)


            self.goto_menu("Network-WLAN Radio2.4G(Online)-Access Control List")

            for m in self.acl_macs :      #iterate on the MACs to be removed

                self.get_table_column("MAC_Table","MACAddress")   # Table order can change on every remove

                if opt_debug :

                    print("About to remove MAC ["+m+"] from table ",self.macs24_list)
            
                if m in  self.macs24_list :

                    mac_pos = self.macs24_list.index(m)
                    
                    if opt_debug :
                        print("MAC position in MAC_TABLE="+str(mac_pos))

                    self.browser.find_element(By.ID, "Btn_Delete"+ str(mac_pos)).click()
                    sleep(20)       # wait some time for router cfg reSync
                    
                else :
                
                    print("Warning: MAC ["+ m + "] not existent in current ACL MAC Table for 2.4GHz SSID.")
                    
    def set_mac_filter_mode(self, mode):
        """
        Method to set MAC_FILTER table mode.

        Supported modes on ZTE F680 router: [   "Block":    Deny access to all MAC table adresses
                                                "Disabled": Disable MAC filter
                                                "Permit":   Allow access only to all MAC Table Addresses
                                            ]
        """
        if self.hw_model == masmovil1:

            self.goto_menu("Network-WLAN Radio2.4G(Online)-Access Control List")
            self.browser.find_element(By.ID, "Frm_Mode").click()
            dropdown = self.browser.find_element(By.ID, "Frm_Mode")
            dropdown.find_element(By.XPATH, "//option[. = '"+mode+"']").click()

    def wait_for(self,e_type, e_name):

        delay = 10  # seconds
        try:
            WebDriverWait(self.browser, delay).until(EC.presence_of_element_located( (By.CLASS_NAME, e_name)))
            #WebDriverWait(self.browser, delay).until(EC.presence_of_element_located( (e_type, e_name)))
            #    break

        except TimeoutException:
                print("Loading took too much time!")


####################################################################################################################
#
#                   FUNCTIONS
#
####################################################################################################################


def check_params():

    global  jobs, maclist, opt_add, opt_debug, opt_dev_name, opt_ls, opt_rm, opt_set, set_mode
    
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

    #parser = argparse.ArgumentParser(description='Manage some IBM Technical Documents.')
    
    #
    # ere argument, required to search from some docs
    #
    parser.add_argument('router_tag',
            help='Router model. Supported models: ZTE_F680')

    #
    # Debug option
    #
    parser.add_argument('-d', action='store_true',
                        help='Debug Mode ON')

    #
    # Add MACs option
    #
    parser.add_argument('-a', nargs=1,
                        help='Add new MACs to ACL Ex: -a "MAC1 MAC2 ... MACn"')

    #
    # Remove MACs option
    #
    parser.add_argument('-r', nargs=1,
                        help='Remove MACs from ACL. Ex: -r "MAC1 MAC2 ... MACn"')

    #
    # List assets description option
    #
    parser.add_argument('-l', action='store_true',
                        help='List current \n ACL table')
    #
    # Set MAC table mode option
    #
    parser.add_argument('-s', nargs=1,
                        help="""Set MAC table working mode. Possible modes are:

					ZTE F680 => {}
						
						Block 		: Deny access only to all MAC Table adresses
						Disabled	: MAC Table filtering OFF
						Permit		: Allow access only to all MAC Table adresses
""".format(str(mac_modes)))


    args = parser.parse_args()
    #args = parser.parse_args(['-a','647033991b78 d0ff9816b558 a8db03d342bb a0a4c5700201 a8c9edf84300','gpfs' ])

    opt_add     = args.a
    opt_debug   = args.d
    opt_dev_name= args.router_tag
    opt_ls      = args.l
    opt_rm      = args.r
    opt_set     = args.s
    
    if opt_add:
        
        for item in args.a[0].split(" ") :
            
            if len(item) != 12: # Check for MAC contains 12 characters
                print("Warning: provided MAC ["+item+"] doesn't contain 12 characters. MAC skipped!")
            else :
                print("Adding MAC: "+item)
                maclist2.append(item)
                jobs += 1

        # future: check if maclist contains only hex digits

    if opt_debug:
        print("Recovered Command Line Arguments: "+str(args))
        print("MACs to remove: ",maclist)
        print("MACs to add: ",maclist2)

    if opt_rm:

        for item in args.r[0].split(" ") :
            
            if len(item) != 12: # Check for MAC contains 12 characters
                print("Warning: provided MAC ["+item+"] doesn't contain 12 characters. MAC skipped!")
            else :
                print("Removing MAC: "+item)
                maclist.append(item)
                jobs += 1

    if opt_set:

        set_mode = args.s[0]
                  
        if set_mode not in mac_modes : # Check for valid mode
            print("Warning: provided MAC mode ["+set_mode+"] is not valid. Possible values:",mac_modes)
        else :
            print("Setting MAC table mode to: "+set_mode)
            jobs += 1


# END check_params()

####################################################################################################################
#
# MAIN
#
####################################################################################################################

check_params()

#
# MAC Adresses to manage
#
ari_phone = "647033991b78"
ari_tab = "d0ff9816b558"
ari_acer ="xxx"
jul_phone = "a8db03d342bb"
jul_asus  = "a0a4c5700201"
ps4 = "e8d81951dc59"
brix = "40e2300d960f"
eli_acer = "7ce9d3564167"
adri_phone = "a8c9edf84300"



#
# Supported Router Models
#
masmovil1 = 'ZTE_F680'
router  = masmovil1
router2 = 'Jazztel'

device_url = {  router :          'http://192.168.1.1/',
                router2 :         'http://www.bancopopular.es/'
              }

if jobs :

    # device = new instance of WifiRouter class
    device = WifiRouter(router, device_url[router])

    # Open device home page and login 
    device.login(user,mykey)

    if opt_add:      # Adding MACs from router ACL table
        device.add_acl(maclist2)

    if opt_rm:      # removing MACs to router ACL table
        device.rm_acl(maclist)

    if opt_set:      # Set MAC table mode
        device.set_mac_filter_mode(set_mode)

    # Close Webdriver & Browser
    device.quit()


print("Done!")
