####      R script to color a phylogenetic tree.
#### Janet Young jayoung at fhcrc.org
####   if you use this for a publication, please:
####     (a)  cite the ape paper (Paradis et al, Bioinformatics, 2004)
####     (b)  cite my paper (Young and Trask, Trends in Genetics, 2007)

############### specify input files #############

#### tree file, in phylip format
#treefile<-"mytree.phy"
treefile 
< 
-"V1Rstouse080922primate 
.fa.seqsover0.6.fa.degapped.phy.distJTT.NJtree.names"
#### classes file - should be tab-delimited - specifies category for  
each gene
#### format: gene name, class name
classesfile<-"simplecategories.txt"

#### colors file - tab-delimited - specifies a color for each category
#### format: class name, color name (see traskdata/help/R/Rcolors.txt  
for list)
colorsfile<-"categoriesandcolors.txt"

#### if desired, a list of genes for which we want the branch widths  
thicker.
#### I was using this to give intact genes thicker branches than  
pseudogenes
#### simply a list of genes, one per line
#### if you don't care about this, can give a fake file name or  
comment it out
##intactfile<-"intactlist.txt"
intactfile<-"V1Rstouse080922intactlist.txt"

### At some point I might implement code to plot bootstrap values -
### there are a few leftover lines in the script related to that

### Specify tree with bootstrap values, also from phylip
### bootstraptreefile<-"fakeboottree.txt"

############### specify parameters #############

### if, and where to place the legend
plotlegend <- "yes"  ## "yes" or "no"
legendposition<-"bottomright"
numlegendcolumns <- 1
legendtextsize <- 1

#### whether to use intact list file to make some branches thicker,
#### also specify how thick to make them
useintactlist <- "yes"  ## "yes" or "no"
regularthickness <- 0.5
thickerthickness <- 1.5

### if, and where to place the scalebar
### (note that scale bar may appear in bottom left)
addscale <- "yes"   ## "yes" or "no"
scalepositionX <- "right"   ### "left" or "right"
scalepositionY <- "top"   ### "top" or "bottom"
scalesize <- 0.1   ## length, in units of tree

### some branches may have negative length. do we want to make
### their length zero?
makenegbrancheszero <- "yes"   ## "yes" or "no"

### the color to use for plotting branches whose descendents are
### a mix of categories
mixedbranchcolor<-"black"

#### label the tips with gene names
showtiplabels <- TRUE ### TRUE or FALSE

### what type of plot to make
plottype<-"phylogram"
#plottype<-"cladogram"
#plottype<-"unrooted"
#plottype<-"radial"
#plottype<-"fan"

### whether to plot the bootstrap values. not yet implemented
#plotbootstrap<-FALSE


############## check the input files exist #################

filewarningflag <- "no"
filewarnings <- vector()
if (!file.exists(treefile)) {
     filewarningflag <- "yes"
     filewarnings<-append(filewarnings,treefile)
}
if (!file.exists(colorsfile)) {
     filewarningflag <- "yes"
     filewarnings<-append(filewarnings,colorsfile)
}
if (!file.exists(classesfile)) {
     filewarningflag <- "yes"
     filewarnings<-append(filewarnings,classesfile)
}
if (useintactlist == "yes") {
     if (!file.exists(intactfile)) {
         filewarningflag <- "yes"
         filewarnings<-append(filewarnings,intactfile)
     }
}
if (filewarningflag == "yes") {
    print ("The following file(s) could not be found in the current  
directory:")
    print (filewarnings)
    stop()
}

############## script #################

library(ape)
X11(width=7.5,height=10)

outfile<-paste(treefile,"colortreenew.ps",sep=".")
outfilepdf<-paste(treefile,"colortreenew.pdf",sep=".")

### read the input files
colors<-read.delim(colorsfile,header=FALSE,row.names=1)

### check the colors exist
plaincols <- as.character(unique(colors[,1]))
for (i in 1:(length(plaincols))) {
    temp<-try(col2rgb(plaincols[i]))
    if(class(temp)=="try-error") {
        stop (paste("no such color as ",plaincols[i]))
    }
}

classes<-read.delim(classesfile,header=FALSE,row.names=1)
tree<-read.tree(treefile)

isitrooted<-is.rooted(tree)

edges<-tree$edge
dim<-dim(edges)
edgecolors<-as.character( vector(length=dim(edges)[1]))

tipnames<-tree$tip.label
tipnames<-sub(".frame1pep.fasta","",tipnames)
branchlengths<-tree$edge.length

### maybe fix negative branch lengths (change to 0)
if (makenegbrancheszero == "yes") {
     for (i in 1:length(branchlengths)) {
         if (branchlengths[i] < 0) {branchlengths[i] <- 0}
     }
}
newtree<-tree
newtree$edge.length<-branchlengths

### figure out colors for each tip (tipcolors)
tipclasses<-as.character(classes[tipnames,1])
tipcolors<-as.character(colors[tipclasses,1])
if (length(grep ("TRUE",is.na(tipcolors)))>0) {
     badclasses<-tipclasses[is.na(tipcolors)]
     print(badclasses)
     temp<-paste("warning ",table(is.na(tipcolors))["TRUE"],
                 " tips had no value in the colors file",sep="")
     stop(temp)
}

### work out immediate descendents for each node
immediatedescendents<-list()
for (i in 1:dim[1]) {
     son1 <- as.character(edges[i,1])
     son2 <- as.character(edges[i,2])

     if (son1 %in% names(immediatedescendents) ) {
        immediatedescendents[[son1]]<- 
append(immediatedescendents[[son1]],son2)
     } else {
        immediatedescendents[[son1]]<-c(son2)
     }
}

### figure out edgewidths (if the flag is set to do this)
edgewidths<-rep(regularthickness,length(edgecolors))
if (useintactlist == "yes") {
      intactlist <- read.delim(intactfile,header=FALSE)
      ### fix some odd names particular to my input files
      intactlist <- gsub("_ORF","",intactlist[,1])
}

### work out colors for nodes
for (i in 1:dim[1]) {
     son2 <- edges[i,2]
     if (node.depth(tree)[son2] > 1) {
        ### non-tips
        alldescendents<-immediatedescendents[[as.character(son2)]]
     } else {
        ### tips
        alldescendents<-son2
        ### if flag is set, test to see if it's in the intact list
        if (useintactlist == "yes") {
            if (tipnames[son2] %in% intactlist) {
                edgewidths[i] <- thickerthickness
            }
        }
     }

     ### iterate through alldescendents until there are no non-tip
     ### nodes left. replace each non-tip node by its descendents.
     sumdepth<-sum(node.depth(tree)[as.numeric(alldescendents)])
     while (sumdepth > length( alldescendents) ) {
        for (j in 1: length(alldescendents)){
           thisnode<-as.numeric(alldescendents[j])
           if (node.depth(tree)[thisnode] > 1) {
               alldescendents<-alldescendents[-j]
               alldescendents<-append(alldescendents,
                      immediatedescendents[[as.character(thisnode)]])
           }
        }
        sumdepth<-sum(node.depth(tree)[as.numeric(alldescendents)])
     }

     ### now we have all the tip descendents, we can look at the colors.
     thesenames<-tipnames[as.numeric(alldescendents)]
     theseclasses<-as.character(classes[thesenames,1])
     thesecolors<-unique(colors[theseclasses,1])
     if (length(thesecolors) == 1) {
         edgecolors[i] <- as.character(thesecolors[1])
     } else {
         edgecolors[i] <- mixedbranchcolor
     }
}

### double-check I figured out all the colors:
if (length(grep ("TRUE",is.na(edgecolors)))>0) {
     temp <- paste("warning - could not work out color for ",
           table(is.na(edgecolors))["TRUE"]," edges",sep="")
     stop(temp)
}

myplot <- plot.phylo(newtree, edge.color=edgecolors,
                   edge.width=edgewidths,tip.color=tipcolors,
                   label.offset=0.02 ,font=1 ,main="", cex=0.35,
                   no.margin=TRUE, cex.main=0.5,
                   show.tip.label=showtiplabels, type=plottype)

title(main=treefile,cex.main=0.8,line=-1)
if(plotlegend == "yes") {
     legend(legendposition,legend=rownames(colors),
            col=as.character(colors[,1]),pch=20,
            ncol=numlegendcolumns,cex=legendtextsize)
}
if(addscale == "yes") {
    if (scalepositionX == "left") {
        scalepositionXtrans<-0
    }
    if (scalepositionX == "right") {
        scalepositionXtrans<- 0.9 * myplot$x.lim[2]
    }
    if (scalepositionY == "bottom") {
        scalepositionYtrans<-0
    }
    if (scalepositionY == "top") {
        scalepositionYtrans<-myplot$y.lim[2]
    }
    add.scale.bar(x=scalepositionXtrans,y=scalepositionYtrans,
                  length=scalesize)
}

#### pause so I can see tree up on the screen
Sys.sleep(3)

### output as both postscript and pdf
dev.print(postscript,file=outfile,horizontal=FALSE)
dev.print(pdf,file=outfilepdf)
dev.off()

### if something went wrong, I might want to examine all those objects  
to
### figure out why, so save everything, as the code runs slowly on big  
trees
save.image(file="colortree.Rdata")

q(save="no")

