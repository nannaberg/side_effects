#!/bin/bash


# outcommented this -> it is too much to connect to the same 12000 websites 8 times in a row
# printf -- "-------making database csv's-------\n\n"
# for file in sideeffect_lists/*.txt
#     do
#         printf -- "---making database for %s---\n" "$file"
#         python3 doit3.py $file 
#         printf -- "---done---\n\n" 
# done
printf -- "-------converting csv's to xlsx-------\n\n"
cd databases/
for file in *.csv
    do 
        printf -- "---converting csv to xlsx for %s---\n" "$file"
        python3 ../convert_csv_to_xlsx.py $file 
        printf -- "---done---\n\n" 
done
printf -- "---all done---\n\n"