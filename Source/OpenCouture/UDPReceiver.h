// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Runtime/Sockets/Public/Sockets.h"
#include "Runtime/Networking/Public/Networking.h"
#include "UDPReceiver.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnMaskReceived, UTexture2D*, Texture);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnWebcam, UTexture2D*, Texture);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnCoordinatesReceived, FString, Cordinates);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnCoordinatesWorldReceived, FString, CordinatesWorld);

USTRUCT()
	struct FImagePacketData
{
	GENERATED_BODY()

	TMap<uint16, TArray<uint8>> PacketMap;
	int32 TotalPackets = 0;
	int32 ReceivedPackets = 0;
};

UCLASS()
class OPENCOUTURE_API AUDPReceiver : public AActor
{
	GENERATED_BODY()
	
public:	
	// Sets default values for this actor's properties
	AUDPReceiver();

	UPROPERTY(BlueprintAssignable, Category = "UDP")
	FOnMaskReceived OnMaskReceived;  // Event für Blueprint
	UPROPERTY(BlueprintAssignable, Category = "UDP")
	FOnWebcam OnWebcam;  // Event für Blueprint
	UPROPERTY(BlueprintAssignable, Category = "UDP")
	FOnCoordinatesReceived OnCoordinatesReceived;  // Event für Blueprint
	UPROPERTY(BlueprintAssignable, Category = "UDP")
	FOnCoordinatesWorldReceived OnCoordinatesWorldReceived;  // Event für Blueprint

protected:
	// Called when the game starts or when spawned
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

public:	
	// Called every frame
	virtual void Tick(float DeltaTime) override;
private:
	void TimedReceiveCheck();
	void StartUDPReceiver();
	void RecvUDPData(FSocket*, int);
	void RecvWebcam(TArray<uint8>);
	void RecvMask(TArray<uint8>);
	void RecvTracking(TArray<uint8>);
	void RecvTrackingWorld(TArray<uint8>);
	//	void UDPReceiverFunction(const FArrayReaderPtr& Reader, const FIPv4Endpoint& Endpoint);

	FSocket* ListenSocketTracking;
	FSocket* ListenSocketWebcam;
	FSocket* ListenSocketMask;
	FUdpSocketReceiver* UDPReceiver;
	FTimerHandle UDPListenHandle;

	TMap<uint32, FImagePacketData> ImagePacketMap;
	TMap<uint32, FImagePacketData> ImagePacketMapMask;
};
