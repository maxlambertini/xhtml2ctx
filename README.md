xhtml2ctx
=========

A simple command line tool that converts XHTML files into TeX/ConTeXt files, respecting their structures. 

It is not meant to magically convert such files into press-ready documents; on the contrary, XHTML2CTX is
a tool to ease such conversion. While most conversion results will compile correctly, the authow must 
nevertheless add its own flair to produce a final document with the desired layout and style. 

## Usage

`xhtml2ctx.py STDIN OPTIONS`

### Options

* __-c, --split-chapters__ : Tell the program to generate a separate .tex file for each `<h1>` tag. That is, every chapter gets its own file. 
* __--columns=<number>__ : Set the number of columns of every chapter. Default is 1. Be aware that only chapters' body is formatted into columns: chapters' titles are rendered in a single column spanning all of the page width. 
* __--css-classes=class1,class2,..,class-n__ : DIVs and Ps whose class attributes match the ones in the list specified in this parameter are rendered as a custom framed text block. 
* __--float-classes=class1,class2,..,class-n__ : Similar to `--css-classes`, but blocks are buffered and rendered as floating objects, detached from main text flow. 
* __--output=file__ : set the output filename. A .tex extension will be appended. 
* __--preamble-file=<file>__ : Tell the program to use a pre-existing .tex file as its document preamble (typescript definition, format definition, etc. etc.)
* __-s, --columnset__ : this flag tells the program to use columnsets instead of columns when rendering files. 
* __--span-classes=class1,class2,..,class-n__ : SPANs whose class attributes match the ones in the list are converted into custom character-level macros. 
* __-t, --floating-tables__ : Tables are treated as floating objects

### Future Developments

* Adding an option to tell XHTML2CTX what the root element is, something similar to JQuery selectors
* Leveraging ConTeXt's environment features. 


