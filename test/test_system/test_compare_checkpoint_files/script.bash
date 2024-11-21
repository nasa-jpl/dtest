#!/bin/bash
#
# Test compareCheckpointFiles

compareCheckpointFiles alpha.checkpoint beta.checkpoint
if [ $? -eq 0 ]
then
    echo "ERROR: comparison of alpha.checkpoint and beta.checkpoint should have showed differences"
    exit 2
fi
echo -n .

compareCheckpointFiles one.checkpoint two.checkpoint
if [ $? -ne 0 ]
then
    echo "ERROR: comparison of one.checkpoint and two.checkpoint should have shown no (significant) differences"
    exit 2
fi
echo -n .

compareCheckpointFiles one.checkpoint one.checkpoint
if [ $? -ne 0 ]
then
    echo "ERROR: comparison of one.checkpoint with itself should have shown no differences"
    exit 2
fi
echo -n .

echo
echo 'OK'
