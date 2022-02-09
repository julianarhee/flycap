
ls *.avi | while read each; do echo "file '$each'" >> movlist.txt; done

outpath="../$1.avi"
echo $outpath

ffmpeg -f concat -i movlist.txt -c copy $outpath
