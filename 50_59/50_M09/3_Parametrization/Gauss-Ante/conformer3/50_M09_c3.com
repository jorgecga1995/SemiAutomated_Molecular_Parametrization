%chk=50_M09_c3_OpFr.chk
%nprocshared=92
%mem=350Gb
#p MaxDisk=1TB mp2/aug-cc-PVTZ pop=mk iop(6/33=2,6/41=10,6/42=17) scf=tight prop=FitCharge Geom=Checkpoint

MP2 ESP for 50_M09_c3    

0   1


