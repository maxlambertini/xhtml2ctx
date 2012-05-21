#!/usr/bin/python

import sys, getopt
from xml.dom import minidom

preamble = """
\\enableregime[utf]
\\useregime[utf]
\setupframedtexts[frame=off,offset=none]

"""

tagDic = {
	u"h1" :( "\n\\chapter{" , "}\n" ),
	u"h2" :( "\n\\section{" , "} " ),
	u"h3" :( "\n\\subsection{" , "} " ),
	u"h4" :( "\n\\subsubsection{" , "} " ),
	u"h5" :( "\n\\subsubsection{" , "} " ),
	u"h6" :( "\n\\subsubsection{" , "} " ),
	u"p" :( "\n\n" , "\n\n" ),
	u"div" :( "\n\n" , "\n\n" ),
	u"dd" :( "\n\n" , "\n\n" ),
	u"li" : ("\n\\item ", "\n\n"),
	u"ol" : ("\n\\startitemize[n,packed]\n","\n\\stopitemize\n"),
	u"ul" : ("\n\\startitemize[1,packed]\n","\n\\stopitemize\n"),
	u"dl" : ("\n\\startitemize[1,packed]\n","\n\\stopitemize\n"),
	u"dt" : ("\n\\head {","}\n\n"),
	u"pre" : ("\n\\starttyping\n","\n\\stoptyping\n"),
	u"blockquote" : ("\n\\startnarrower\n","\n\\stopnarrower\n"),
	u"b" : ("{\\bf ","} "),
	u"span" : ("",""),
	u"strong" : ("{\\bf ","} "),
	u"em" : ("{\\em ","} "),
	u"i" : ("{\\em ","} "),
	u"u" : ("{\\em ","} "),
	u"cite" : ("{\\it ","} "),
	u"big" : ("{\\tfa ","} "),
	u"small" : ("{\\tfx ","} "),
	u"table" : ("\n\\bTABLE\n","\n\\eTABLE\n"),
	u"thead" : ("\n\\bTABLEhead\n","\n\\eTABLEhead\n"),
	u"tbody" : ("\n\\bTABLEbody\n","\n\\eTABLEbody\n"),
	u"tr" : ("\n\\bTR\n","\n\\eTR\n"),
	u"th" : ("\n\\bTH##SPAN##\n","\n\\eTH\n"),
	u"td" : ("\n\\bTD##SPAN##\n","\n\\eTD\n")
}

tagFloats = {
	u"table" : ("\n\n\\startbuffer[ta##PARA##]\n\\bTABLE\n\n",
	            "\\eTABLE\n\\stopbuffer\n\\placetable[here,force,center][t##PARA##]{Describe Table Here}{\\getbuffer[ta##PARA##]}\n\n"),
	u"p_float" 
			: ("\n\n\\startbuffer[buf##PARA##]\n\\start##NAME##\n",
	          "\\stop##NAME##\n\\stopbuffer\n\\place##NAME##[here,force,center][t##PARA##]{Describe ##NAME## Here}{\\getbuffer[buf##PARA##]}\n\n"),
	u"div_float" 
			: ("\n\n\\startbuffer[buf##PARA##]\n\\start##NAME##\n",
	          "\\stop##NAME##\n\\stopbuffer\n\\place##NAME##[here,force,center][t##PARA##]{Describe ##NAME## Here}{\\getbuffer[buf##PARA##]}\n\n"),
	u"p"     : ("\n\\start##PARA##\n","\n\\stop##PARA##\n"),
	u"div"   : ("\n\\start##PARA##\n","\n\\stop##PARA##\n")
}



class TexConverter:
	
	def __init__(self):
		self.elements_processed = 0
		self.css_classes = []
		self.float_classes = []
		self.span_classes = []
		self.floating_tables = False
		self.xmldoc = None
		self.sBufOut = ""
		self.preamble = preamble
		self.partial_doc = False
		self.body_container = "body"
		self.char_macros = []
		self.columns = 1
		self.preamble_file = None
		self.output_file = None
		self.split_chapters = False
		self.create_index = True
		self.use_columnset = False
		self.chapter_names=["_start"]
		self.stop_words = []
		self.headers = [u"h1",u"h2",u"h3",u"h4",u"h5",u"h6"]
		self.punctuation = [u".",u",",u"?",u"!",u":",u";" ]
		self.alphabet="abcdefghijklmnopqrstuvwxyz"

	def read_stopwords (self, filename = "stopwords.txt"):
		with (open (filename,"r")) as file:
			self.stop_words = [line.replace("\n","").lower() for line in file.readlines()]
	
	def process_element(self, element):
		self.elements_processed += 1
		if (len(element.childNodes) > 0):
			(startNode,endNode) = tagDic[element.nodeName]
			
			# process headers ---
			if element.nodeName == u"h1":
				self.chapter_names.append(element.childNodes[0].nodeValue.replace(" ","_"))
			
			# get the title, split it into words and for every word not in list place title, index
			if (element.nodeName in self.headers):
				header_name = element.childNodes[0].nodeValue
				for p in self.punctuation:
					header_name = header_name.replace(p,"")
				header_items = header_name.lower().split()
				endNode += " \\index{%s}" % (header_name)
				for hi in header_items:
					if (not (hi in self.stop_words) or not (hi[0] in self.alphabet)) and hi[-3:] != "ing":
						endNode += " \\index{%s}" % (hi.capitalize())
				endNode += "\n"
			
			if element.nodeName == u"td" or element.nodeName == u"th":
				if element.attributes.has_key("colspan") or element.attributes.has_key("rowspan"):
					td_pars = []
					if element.attributes.has_key("rowspan"):
						td_pars.append("nr="+str(element.attributes["rowspan"].nodeValue))
					if element.attributes.has_key("colspan"):
						td_pars.append("nc="+str(element.attributes["colspan"].nodeValue))
					span = "["+",".join(td_pars)+"]"
					startNode = startNode.replace("##SPAN##",span)
				else:
					startNode = startNode.replace("##SPAN##","")
			if element.nodeName == u"table" and self.floating_tables:
				(startNode,endNode) = tagFloats[element.nodeName]
				startNode = startNode.replace("##PARA##",str(self.elements_processed))
				endNode = endNode.replace("##PARA##",str(self.elements_processed))
				
			if (element.nodeName == u"p" and element.attributes.has_key("class") and len(self.float_classes) > 0):
				for cls in self.float_classes:
					cls_items = element.attributes["class"].nodeValue.split(" ")
					for cls_item in cls_items:
						if cls_item.upper() == cls.upper():
							(startNode,endNode) = tagFloats[element.nodeName+u"_float"]
							startNode = startNode.replace("##PARA##",str(self.elements_processed))
							startNode = startNode.replace("##NAME##",cls_item)
							endNode = endNode.replace("##PARA##",str(self.elements_processed))
							endNode = endNode.replace("##NAME##",cls_item)

			if (element.nodeName == u"span" and element.attributes.has_key("class") and len(self.span_classes) > 0):
				for cls in self.span_classes:
					cls_items = element.attributes["class"].nodeValue.split(" ")
					for cls_item in cls_items:
						if cls_item.upper() == cls.upper():
							startNode = "\\CM"+cls_item.replace("_","")+"{"
							endNode= "} "
							
							
			if (element.nodeName == u"p" and element.attributes.has_key("class") and len(self.css_classes) > 0):
				for cls in self.css_classes:
					cls_items = element.attributes["class"].nodeValue.split(" ")
					for cls_item in cls_items:
						if cls_item.upper() == cls.upper():
							(startNode,endNode) = tagFloats[element.nodeName]
							startNode = startNode.replace("##PARA##",cls_item)
							endNode = endNode.replace("##PARA##",cls_item)
							
			if (element.nodeName == u"div" and element.attributes.has_key("class") and len(self.float_classes) > 0):
				for cls in self.float_classes:
					cls_items = element.attributes["class"].nodeValue.split(" ")
					for cls_item in cls_items:
						if cls_item.upper() == cls.upper():
							(startNode,endNode) = tagFloats[element.nodeName+u"_float"]
							startNode = startNode.replace("##PARA##",str(self.elements_processed))
							startNode = startNode.replace("##NAME##",cls_item)
							endNode = endNode.replace("##PARA##",str(self.elements_processed))
							endNode = endNode.replace("##NAME##",cls_item)
													
			if (element.nodeName == u"div" and element.attributes.has_key("class")  and len(self.css_classes) > 0):
				for cls in self.css_classes:
					cls_items = element.attributes["class"].nodeValue.split(" ")
					for cls_item in cls_items:
						if cls_item.upper() == cls.upper():
							(startNode,endNode) = tagFloats[element.nodeName]
							startNode = startNode.replace("##PARA##",cls_item)
							endNode = endNode.replace("##PARA##",cls_item)

							
			element1 = self.xml_doc.createElement("#text")
			element1.nodeValue = startNode
			element2 = self.xml_doc.createElement("#text")
			element2.nodeValue = endNode
			element.insertBefore(element1,element.childNodes[0])
			element.appendChild(element2);
		


	def traverseNodes (self,node):
		if (tagDic.has_key (node.nodeName)):
			self.process_element(node)
		for n in node.childNodes:
			self.traverseNodes(n)
		if (node.nodeValue != None):
			self.sBufOut = unicode(self.sBufOut) + unicode(node.nodeValue)
			#sOut = sOut.replace ("{ ","{")
			#sOut = sOut.replace (" }","}")
			#print sOut,

	def usage(self):
		sOut = """
xhtml2tex.py -- A simple XHTML to ConTeXt parser

Usage: xhtml2tex.py OPTIONS STDIN STDOUT

OPTIONS:
-t, --floating-tables         
    Tables are treated as floats
--css-classes=class1,class2,class3.. 
    DIVs and Ps whose CLASS attribute is decorated with these
	classes are placed into their own named blocks 
--span-classes=class1,class2,class3....
	SPANs containing these CSS classes are converted into custom 
	character-level macros. Minus signs and underscores are wiped 
	out from style names. Camel case is preserved
--float-classes=class1,class2,class3.. 
    similar as --css-classes, but DIVs and P's are converted into floats
--partial-doc
	don't wrap output in a ConTeXt preamble. Useful for merging html 
	docs into one.
--body-container=tagname
	set the HTML element containing the text body. Default is 'body'
--columns=n
	set the number of columns. Default is 1
--preamble-file=<file>
	load the ConTeXt file specified and use it as a preamble
-c, --split-chapters
	split output into multiple files. This option works only if 
	--output file is specified AND --partial-doc is disabled. 
	Output is cut in correspondence of \chapter and \starttext. 
	VERY USEFUL for handling long 
	documents.
-s, --columnset
	use columnset instead of columns. 
--output=file
	redirect the output to <file>
	
-h, --help
   this text                                    
"""
		print sOut


	def analyze_options(self):
		try:
			opts, args = getopt.getopt(sys.argv[1:], "htpcs", \
				["help", "float-classes=","css-classes=","span-classes=",\
				 "floating-tables","partial-doc","body-container=", \
				 "columns=","preamble-file=","split-chapters","columnset",\
				 "output="])
		except getopt.GetoptError,err:
			print str(err)
			self.usage()
			sys.exit(2)
		for o,a in opts:
			if o in ("-t","--floating-tables"):
				self.floating_tables = True
			elif o in ("-h","--help"):
				self.usage()
				sys.exit()
			elif o == "--span-classes":
				self.span_classes  = a.split(",")
				for css in self.span_classes:
					self.char_macros.append ("\\def\\CM%s#1{#1}\n" % (css) )
			elif o == "--css-classes":
				self.css_classes = a.split(",")
			elif o == "--float-classes":
				self.float_classes = a.split(",")
			elif o in("p", "--partial-doc"):
				self.partial_doc = True
			elif o == "--body-container":
				self.body_container = a
			elif o == "--columns":
				try:					
					self.columns = a
				except Exception as exc:
					pass
			elif o == "--preamble-file":
				self.preamble_file = a
			elif o == "--output":
				self.output_file = a
				if self.output_file.lower()[-4:] != ".tex":
					self.output_file = self.output_file+".tex"
			elif o in("-c", "--split-chapters"):
				self.split_chapters = True
			elif o in ("-s","--columnset"):
				self.use_columnset = True
			else:
				assert False, "Unhandled options"
				
		
				
	def convert(self):
		_preamble = '';
		if self.preamble_file != None:		
			try:
				print "preamble file", self.preamble_file
				_preamble = unicode(open(self.preamble_file,'r').read(),"utf-8")
			except:
				_preamble = preamble;
		else:
			_preamble = preamble;

		if self.columns > 1:
			print "columns: ", self.columns
			if self.use_columnset :
				print "using columnset"
				_preamble += "\n\\definecolumnset[document][n=" + self.columns + "]\n"
				tagDic[u"h1"] = ("\\stopcolumnset\n\\chapter{" , "}\n\\startcolumnset[example]\n" )
			else:
				print "using columns"
				tagDic[u"h1"] = ("\\stopcolumns\n\\chapter{" , "}\n\\startcolumns[n=" +self.columns + "] " )
			
			
		self.sBufOut = ""
		self.sBufOut = self.sBufOut.encode("UTF-8")
		
		if not self.partial_doc:
			tagDic[self.body_container] = ("\n\\starttext\n","\n\\stopcolumns\n\\page\n\\startcolumns[n=3]\n\\completeindex\\\\stopcolumns\n\\stoptext\n")

		
		if len(self.css_classes) > 0:
			styles = ["rmbf","rmbi","rmit","rmsc","rmsl","rm","ssbf","ssbi","ssit","sssc","sssl","ss","ttbf","ttbi","tit","ttsc","ttsl","tt"]
			h = 0
			for cls in self.css_classes:
				_preamble += u"\\defineframedtext[" + cls + u"][frame=off,offset=none,width=broad,style={\\%s},strut=no,before={\\nowhitespace},after={\\nowhitespace}]\n" % (styles[h % len(styles)])
				h += 1

		if len(self.float_classes) > 0:
			for cls in self.float_classes:
				_preamble += u"\\defineframedtext[" + cls + u"][]\n"
				_preamble += u"\\definefloat[" + cls + u"][]\n"
				
		for macro in self.char_macros:
			_preamble += macro + "\n"
				
		xml_str = unicode("","utf-8")
		lines = sys.stdin.readlines()
		for l in lines:
			xml_str = xml_str + unicode(l,"utf-8")
		
		xml_str = xml_str.replace(u"\n",u" ")
		xml_str = xml_str.replace(u"\r",u" ")
		xml_str = xml_str.replace(u"&nbsp;",u" ")

		self.xml_doc = minidom.parseString(xml_str.encode("utf-8"))
		myitem = self.xml_doc.getElementsByTagName(self.body_container)
			
		self.traverseNodes (myitem[0])
		
		self.sBufOut = self.sBufOut.replace(u"$",u"\\$")
		self.sBufOut = self.sBufOut.replace(u"&",u"\\&")
		self.sBufOut = self.sBufOut.replace(u"_",u"\\_")
		self.sBufOut = self.sBufOut.replace(u"%",u"\\%")
		self.sBufOut = self.sBufOut.replace(u"#",u"\\#")

		if not self.partial_doc:
			self.sBufOut = _preamble + self.sBufOut
			
		
		self.sBufOut = self.sBufOut.encode("utf-8")

		if self.output_file == None:
			print self.sBufOut
		else:
			if not self.split_chapters or self.partial_doc:
				print "Writing to ",self.output_file
				out = open(self.output_file,"w")
				out.write(self.sBufOut)
				out.close()
				print "All done!"
			else:
				# separate preamble from body
				(my_preamble,body) = self.sBufOut.split("\\starttext")				
				# remove stoptext from body
				body = body.replace("\\stoptext","")
				# create chapters
				chapters = body.split("\\chapter")
				
				#save intermediate files
				preamble_file = self.output_file[:-4]+"_preamble.tex"
				with open (preamble_file,"w") as f:
					print "writing preamble to ", preamble_file
					f.write (my_preamble)
				
				cnt = 0
				for chapter in chapters:
					chap_file = "%s_%03d_%s.tex" % (self.output_file[:-4],cnt,self.chapter_names[cnt])
					print "writing chapters to ", chap_file
					with open (chap_file,"w") as f:
						if (cnt == 0):
							f.write(chapter)
						else:
							f.write ("\\chapter"+chapter)
					cnt = cnt +1
				
				#written all intermediate files, now assembling everything!
				
				print "assembling..."
				sOut = "\\input %s \n\n\\starttext\n\n" % (preamble_file)
				print "assembled...",preamble_file
				for r in range (0,len(chapters)):				
					print "assembled...", "%s_%03d_%s" % (self.output_file[:-4],r,self.chapter_names[r])
					sOut = sOut + "\\input %s_%03d_%s.tex\n" % (self.output_file[:-4],r,self.chapter_names[r])
				
				sOut = sOut + "\n\n\\stoptext\n"
				with open (self.output_file[:-4]+".tex","w") as f:
					f.write (sOut)

				sOut = sOut + "\n\n\\stoptext\n"
				with open ("complete_"+self.output_file,"w") as f:
					f.write (self.sBufOut)
				
				#that's all
				print "Data written on ",self.output_file," all done!"

				
				
	
def main():
	tc = TexConverter();
	tc.read_stopwords()
	tc.analyze_options()
	tc.convert()
	
if __name__ == "__main__":
    main()
	

