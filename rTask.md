
TASK 7/23/25

1.
no need to think abut the compression ratio

## Draco-for-3DGS
check
change the 16 bits to 0 bits  0 bit means lossless
if i set it as 0 i will not lose any information and the we will keep the order
use the diff cmd first if its differnt use https://github.com/SYJINTW/GS-Interface.git

## Draco original
2. check if we compress the mesh . Try to compress the colored mesh (yuan chun will give color mesh later)
- make sure that we use lossless way to (check in the original readme) and make sure that the order will not change
- way to check diff (cmd to see if the two data are differnet) maybe write a reader to checkk if tthe informatin are the same
- (the reader trimesh (python library) to check if the information of the mesh are the same like vertex face triancgle color if they are the same)


## Draco-for-3DGS
3. change all the information except the sh (color) change it all to 0 but keep the color and compress using the lossless way
then i compress it with the lossless way and check if the two data ( check the file size )
TO CHANGE THE 3DGS INFORMAION WE CAN USE https://github.com/SYJINTW/GS-Interface.git

4. Check the draco 3dgs code
- small experiment try to not compress rotation ex delete the rotation part(like dont need to read the rotation)

feed the original 3dgs --> compress it --> then decode it --> after we unpacked we wont have the rotation




# -------------------------------------------------------------------------

# 28/7/26
## Draco original
1. check if we compress the mesh . Try to compress the colored mesh (yuan chun will give color mesh later)
- make sure that we use lossless way to (check in the original readme) and make sure that the order will not change
- way to check diff (cmd to see if the two data are differnet) maybe write a reader to checkk if tthe informatin are the same
- (the reader trimesh (python library) to check if the information of the mesh are the same like vertex face triancgle color if they are the same)

2.profiling the decoding time  (ask yuan chun for the two data set -big and small mesh and gaussion)

decode it 5 time each
for the mesh and 3dgs
compress it lossless

see the average time that it take to encode and decode

do it 5 times

my CPU




## Draco-for-3DGS
3. remove attribute
skip reading  the scale and the normal

only keep
position xyz
color f_dc
f_rest
opacity

chekc if its the same xyz and opacity and color is the same


some slide to tell how i remove the attribute (show the code and how i implement it )

chekc if its the same xyz and opacity and color is the same




# 8/6/26

Keep the original

and always update the readme and version control


# Task1
## kinda like draco but for mesh

git@github.com:nahathaiw/meshoptimizer.git
try to run this set up the enviroment
try to encode and decode and analyze it -- lossless way and check the number of faces and vertics  if its the same


dowload this to render the mesh -- make sure if i will see the color

https://www.meshlab.net/

try to compress mesh with lossless



Task 2
https://fraunhoferhhi.github.io/Self-Organizing-Gaussians/
compress the 3d gaussian using this project


compress the 3d gaussion with the lossless way but if there no lossless way tell the limitation


use this to dowload the sample dataset
use the hotdog one (using blender gaussion splaat)
https://nerfbaselines.github.io/
check if the attribute vertices faces and stuff are changing or not


### WRITE THE READ ME FOR THESE TWO PROJECT FOR IT TO BE EASLIY USE BY OTHER
