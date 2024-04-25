#!/bin/sh

#Wait until is solution plug is connected
while ! snapctl is-connected active-solution 
do 
  sleep 5 
done

export LC_ALL=C   

#Create folder
folder_name=active
directory="$SNAP_COMMON/solutions/activeConfiguration/$folder_name"

if [ ! -d "$directory"]; then
	mkdir $directory
    echo $directory
fi

#Move to the working directory
cd $directory

# Make sure the configuration directory exists
if [ ! -d "./Example" ]; then   #Attention with putting a ./ this will check if in the directory is a Target folder
  mkdir ./Example  #Create target folder if it does not exist
  cp $SNAP/bin/Example/Example ./Example/Example  #Copy target file that is located in the bin file when the snap is created to the $SNAP_COMMON/solutions/activeConfiguration/novnc/Target folder
fi