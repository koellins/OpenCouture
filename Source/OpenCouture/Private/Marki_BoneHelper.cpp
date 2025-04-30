#include "Marki_BoneHelper.h"

void UMarki_BoneHelper::AddBoneRotationOffset(UPoseableMeshComponent* PoseableMesh, FName BoneName, FRotator RotationOffset)
{
	if (!PoseableMesh || BoneName.IsNone()) return;

	// Hole aktuelle Rotation im Bone-Space
	const FRotator CurrentRotation = PoseableMesh->GetBoneRotationByName(BoneName, EBoneSpaces::ComponentSpace);

	// Neue Rotation berechnen
	const FRotator NewRotation = (CurrentRotation + RotationOffset).GetNormalized();

	// Setze die Rotation
	PoseableMesh->SetBoneRotationByName(BoneName, NewRotation, EBoneSpaces::ComponentSpace);
}
