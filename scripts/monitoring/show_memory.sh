virsh list --name | xargs -L1 -I{} sh -c "echo {}; virsh dommemstat {} | grep rss"
virsh list --all --name | grep -v cplane | xargs -L1 -I{} virsh start {}