#!/bin/bash
for i in {1..3}
do 
    cat my_input_qa_nuralogix.txt | xargs python measure.py
    # sleep 5
done 
