# to activate do: 
# source define_environment.sh

export PETSC_DIR=/users/srio/OASYS_VE/comsyl_srio/petsc 
export PETSC_ARCH=arch-linux2-c-opt
export SLEPC_DIR=/users/srio/OASYS_VE/comsyl_srio/slepc-3.7.3
source /users/srio/OASYS_VE/oasys1env/bin/activate
echo "PETSC_DIR has been set to: $PETSC_DIR"
echo "PETSC_ARCH has been set to: $PETSC_ARCH"
echo "SLEPC_DIR has been set to: $SLEPC_DIR"
echo "python is from `which python`"
