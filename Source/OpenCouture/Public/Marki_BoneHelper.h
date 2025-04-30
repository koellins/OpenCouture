#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "Components/PoseableMeshComponent.h"
#include "Marki_BoneHelper.generated.h"

UCLASS()
class OPENCOUTURE_API UMarki_BoneHelper : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

	public:
		UFUNCTION(BlueprintCallable, Category = "Bones")
		static void AddBoneRotationOffset(UPoseableMeshComponent* PoseableMesh, FName BoneName, FRotator RotationOffset);
};
