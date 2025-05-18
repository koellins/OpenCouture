// Fill out your copyright notice in the Description page of Project Settings.


#include "UDPReceiver.h"
#include "Sockets.h"
#include "TimerManager.h"
#include "Networking.h"
#include "Engine/Texture2D.h"
#include "ImageUtils.h"
#include "Engine/Texture2DDynamic.h"

#define MAX_PACKET_SIZE 60000

// Sets default values
AUDPReceiver::AUDPReceiver()
{
	PrimaryActorTick.bCanEverTick = false;

}

// Called when the game starts or when spawned
void AUDPReceiver::BeginPlay()
{
	Super::BeginPlay();
	GEngine->AddOnScreenDebugMessage(-1, 5.f, FColor::Red, TEXT("UDP receiver active!"));
	StartUDPReceiver();
}

void AUDPReceiver::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	Super::EndPlay(EndPlayReason);
	if (UDPReceiver)
	{
		delete UDPReceiver;
		UDPReceiver = nullptr;
	}
	if (ListenSocketTracking)
	{
		ListenSocketTracking->Close();
		ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM)->DestroySocket(ListenSocketTracking);
	}
	if (ListenSocketWebcam)
	{
		ListenSocketWebcam->Close();
		ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM)->DestroySocket(ListenSocketWebcam);
	}	
	if (ListenSocketMask)
	{
		ListenSocketMask->Close();
		ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM)->DestroySocket(ListenSocketMask);
	}
}

// Called every frame
void AUDPReceiver::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

}

void AUDPReceiver::StartUDPReceiver()
{
	FIPv4Address Addr;
	FIPv4Address::Parse(TEXT("127.0.0.1"), Addr);

	ListenSocketTracking = FUdpSocketBuilder(TEXT("UDPReceiverSocketTrackig"))
		.AsReusable()
		.BoundToAddress(Addr)
		.BoundToPort(5011)
		.WithBroadcast();
	if (!ListenSocketTracking)
	{
		UE_LOG(LogTemp, Error, TEXT("Tracking-Socket konnte nicht erstellt werden!"));
		return;
	}
	ListenSocketWebcam = FUdpSocketBuilder(TEXT("UDPReceiverSocketWebcam"))
		.AsReusable()
		.BoundToAddress(Addr)
		.BoundToPort(5012)
		.WithBroadcast();
	if (!ListenSocketWebcam)
	{
		UE_LOG(LogTemp, Error, TEXT("UDP-Socket konnte nicht erstellt werden!"));
		return;
	}
	ListenSocketMask = FUdpSocketBuilder(TEXT("UDPReceiverSocketMask"))
		.AsReusable()
		.BoundToAddress(Addr)
		.BoundToPort(5013)
		.WithBroadcast();
	if (!ListenSocketMask)
	{
		UE_LOG(LogTemp, Error, TEXT("UDP-Socket konnte nicht erstellt werden!"));
		return;
	}

	int32 BufferSize = 2 * 1024 * 1024;
	ListenSocketTracking->SetReceiveBufferSize(BufferSize, BufferSize);
	ListenSocketWebcam->SetReceiveBufferSize(BufferSize, BufferSize);
	ListenSocketMask->SetReceiveBufferSize(BufferSize, BufferSize);

	GetWorld()->GetTimerManager().SetTimer(UDPListenHandle, this, &AUDPReceiver::TimedReceiveCheck, 0.033f, true);
}

void AUDPReceiver::TimedReceiveCheck() 
{
	RecvUDPData(ListenSocketTracking, 1);
	RecvUDPData(ListenSocketWebcam, 2);
	RecvUDPData(ListenSocketMask, 3);
}

void AUDPReceiver::RecvUDPData(FSocket* ListenSocket, int index)
{
	if (!ListenSocket) return;
	//GEngine->AddOnScreenDebugMessage(-1, 5.f, FColor::Red, TEXT("UDP Message receive"));
	uint32 Size;
	if (index == 1) {
		while (ListenSocket->HasPendingData(Size))
		{
			uint8 Header[5];
			//uint8 Id[4];
			int32 BytesRead = 0;
			if (!ListenSocket->Recv(Header, 5, BytesRead) || BytesRead != 5)
			{
				GEngine->AddOnScreenDebugMessage(-1, 5.f, FColor::Red, TEXT("UDP Fehler bildgröße!"));
				return;
			}

			uint8 ImageID = Header[0];  // 1 Byte ID
			int32 ImageSize = (Header[1] << 24) | (Header[2] << 16) | (Header[3] << 8) | Header[4];

			//GEngine->AddOnScreenDebugMessage(-1, 5.f, FColor::Red, FString::FromInt(ImageID));
			//GEngine->AddOnScreenDebugMessage(-1, 5.f, FColor::Red, FString::FromInt(ImageSize));

		
			if (ImageSize <= 0 || ImageSize > 65536)
			{
				UE_LOG(LogTemp, Error, TEXT("Ungültige Bildgröße empfangen: %d"), ImageSize);
				return;
			}

			TArray<uint8> ReceivedData;
			ReceivedData.SetNumUninitialized(ImageSize);
			if (!ListenSocket->Recv(ReceivedData.GetData(), ImageSize, BytesRead) || BytesRead != ImageSize)
			{
				UE_LOG(LogTemp, Error, TEXT("Fehler beim Empfangen der Bilddaten"));
				return;
			}

			switch (ImageID)
			{
				case 1:			//TRACKINGDATA
					RecvTracking(ReceivedData);
					break;
				case 2:			//WEBCAM
					RecvWebcam(ReceivedData);
					break;
				case 3:			//MASK
					RecvMask(ReceivedData);
					break;
				case 4:
					RecvTrackingWorld(ReceivedData);
				default:
					break;
			}

		}
	}
	else if (index == 2) 
	{ // Webcam
		uint32 PendingSize;
		while (ListenSocket->HasPendingData(PendingSize))
		{
			uint8 Buffer[MAX_PACKET_SIZE + 10];
			int32 BytesRead = 0;

			if (ListenSocket->Recv(Buffer, sizeof(Buffer), BytesRead))
			{
				if (BytesRead < 10) continue;

				uint32 ImageID;
				uint16 PacketIndex, TotalPackets, PayloadSize;
				FMemory::Memcpy(&ImageID, Buffer, 4);
				FMemory::Memcpy(&PacketIndex, Buffer + 4, 2);
				FMemory::Memcpy(&TotalPackets, Buffer + 6, 2);
				FMemory::Memcpy(&PayloadSize, Buffer + 8, 2);
			//	GEngine->AddOnScreenDebugMessage(-1, 5.f, FColor::Red, FString::FromInt(TotalPackets));
				if (PayloadSize + 10 != BytesRead) continue;
				FImagePacketData& PacketData = ImagePacketMap.FindOrAdd(ImageID);
				if (PacketData.PacketMap.Contains(PacketIndex)) continue;

				TArray<uint8> Packet;
				Packet.Append(Buffer + 10, PayloadSize);

				PacketData.PacketMap.Add(PacketIndex, Packet);
				PacketData.TotalPackets = TotalPackets;
				PacketData.ReceivedPackets++;

				if (PacketData.ReceivedPackets >= PacketData.TotalPackets)
				{
					TArray<uint8> FullData;
					for (uint16 i = 0; i < PacketData.TotalPackets; ++i)
					{
						if (PacketData.PacketMap.Contains(i))
						{
							FullData.Append(PacketData.PacketMap[i]);
						}
						else
						{
							UE_LOG(LogTemp, Error, TEXT("Fehlendes Paket: %d"), i);
							return;
						}
					}

					UTexture2D* NewTexture = FImageUtils::ImportBufferAsTexture2D(FullData);
					if (NewTexture)
					{
						OnWebcam.Broadcast(NewTexture);
					}
					ImagePacketMap.Remove(ImageID);
				}
			}
		}

	}
	else if (index == 3)
	{ // Mask
		uint32 PendingSizeMask;
		while (ListenSocket->HasPendingData(PendingSizeMask))
		{
			uint8 Buffer[MAX_PACKET_SIZE + 10];
			int32 BytesRead = 0;

			if (ListenSocket->Recv(Buffer, sizeof(Buffer), BytesRead))
			{
				if (BytesRead < 10) continue;

				uint32 ImageID;
				uint16 PacketIndex, TotalPackets, PayloadSize;
				FMemory::Memcpy(&ImageID, Buffer, 4);
				FMemory::Memcpy(&PacketIndex, Buffer + 4, 2);
				FMemory::Memcpy(&TotalPackets, Buffer + 6, 2);
				FMemory::Memcpy(&PayloadSize, Buffer + 8, 2);
				//GEngine->AddOnScreenDebugMessage(-1, 5.f, FColor::Red, FString::FromInt(TotalPackets));
				if (PayloadSize + 10 != BytesRead) continue;
				FImagePacketData& PacketData = ImagePacketMapMask.FindOrAdd(ImageID);
				if (PacketData.PacketMap.Contains(PacketIndex)) continue;

				TArray<uint8> Packet;
				Packet.Append(Buffer + 10, PayloadSize);

				PacketData.PacketMap.Add(PacketIndex, Packet);
				PacketData.TotalPackets = TotalPackets;
				PacketData.ReceivedPackets++;

				if (PacketData.ReceivedPackets >= PacketData.TotalPackets)
				{
					TArray<uint8> FullData;
					for (uint16 i = 0; i < PacketData.TotalPackets; ++i)
					{
						if (PacketData.PacketMap.Contains(i))
						{
							FullData.Append(PacketData.PacketMap[i]);
						}
						else
						{
							UE_LOG(LogTemp, Error, TEXT("Fehlendes Paket: %d"), i);
							return;
						}
					}

					UTexture2D* NewTexture = FImageUtils::ImportBufferAsTexture2D(FullData);
					if (NewTexture)
					{
						OnMaskReceived.Broadcast(NewTexture);
					}
					ImagePacketMapMask.Remove(ImageID);
				}
			}
		}
	}
}

void AUDPReceiver::RecvWebcam(TArray<uint8> Data)
{
	UTexture2D* WebcamTex = FImageUtils::ImportBufferAsTexture2D(Data);
	if (WebcamTex)
	{
		//UE_LOG(LogTemp, Log, TEXT("Bild empfangen und konvertiert!"));
		OnWebcam.Broadcast(WebcamTex);
	}
}
void AUDPReceiver::RecvMask(TArray<uint8> Data)
{
	UTexture2D* MaskTex = FImageUtils::ImportBufferAsTexture2D(Data);
	if (MaskTex)
	{
		//UE_LOG(LogTemp, Log, TEXT("Bild empfangen und konvertiert!"));
		OnMaskReceived.Broadcast(MaskTex);
	}
}
void AUDPReceiver::RecvTracking(TArray<uint8> Data)
{
	Data.Add(0);

	FString ReceivedString = FString(UTF8_TO_TCHAR(reinterpret_cast<const char*>(Data.GetData())));
	//UE_LOG(LogTemp, Log, TEXT("Empfangene Daten: %s"), *ReceivedString);
	OnCoordinatesReceived.Broadcast(ReceivedString);
}
void AUDPReceiver::RecvTrackingWorld(TArray<uint8> Data)
{
	Data.Add(0);

	FString ReceivedString = FString(UTF8_TO_TCHAR(reinterpret_cast<const char*>(Data.GetData())));
	//UE_LOG(LogTemp, Log, TEXT("Empfangene Daten: %s"), *ReceivedString);
	OnCoordinatesWorldReceived.Broadcast(ReceivedString);
}

//void AUDPReceiver::UDPReceiverFunction(const FArrayReaderPtr& Reader, const FIPv4Endpoint& Endpoint)
//{
//	uint8 RecvData[65507];
//	int32 BytesRead = 0;
//
//	if (ListenSocket->Recv(RecvData, sizeof(RecvData), BytesRead))
//	{
//		UE_LOG(LogTemp, Warning, TEXT("Received %d bytes"), BytesRead);
//
//		// Hier kannst du das Bild dekodieren
//		TArray<uint8> ImageData;
//		ImageData.Append(RecvData, BytesRead);
//
//		// UE5 Texture aus den empfangenen Daten erstellen
//		
//		UTexture2D* NewTexture = FImageUtils::ImportBufferAsTexture2D(ImageData);
//		if (NewTexture)
//		{
//			UE_LOG(LogTemp, Warning, TEXT("Texture created!"));
//		}
//	}
//}

	//receive packets
//void AUDPReceiver::RecvUDPData()
//{
//	if (!ListenSocket) return;
//
//	uint32 Size;
//	while (ListenSocket->HasPendingData(Size))
//	{
//		TArray<uint8> RecvBuffer;
//		RecvBuffer.SetNumUninitialized(FMath::Min(Size, 65507u));
//
//		int32 BytesRead = 0;
//		TSharedRef<FInternetAddr> Sender = ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM)->CreateInternetAddr();
//
//		if (ListenSocket->RecvFrom(RecvBuffer.GetData(), RecvBuffer.Num(), BytesRead, *Sender))
//		{
//			if (BytesRead < 10) continue; // Header ist 10 Byte: 4 + 2 + 2 + 2
//
//			uint32 ImageID = (RecvBuffer[0] << 24) | (RecvBuffer[1] << 16) | (RecvBuffer[2] << 8) | RecvBuffer[3];
//			uint16 PacketIndex = (RecvBuffer[4] << 8) | RecvBuffer[5];
//			uint16 TotalPackets = (RecvBuffer[6] << 8) | RecvBuffer[7];
//			uint16 PayloadSize = (RecvBuffer[8] << 8) | RecvBuffer[9];
//
//			if (BytesRead < 10 + PayloadSize) continue;
//
//			TArray<uint8> Payload;
//			Payload.Append(RecvBuffer.GetData() + 10, PayloadSize);
//
//			FImagePacketData& PacketData = ImagePacketMap.FindOrAdd(ImageID);
//			if (PacketData.Packets.Num() == 0)
//			{
//				PacketData.Packets.SetNumZeroed(TotalPackets);
//				PacketData.ExpectedPackets = TotalPackets;
//			}
//
//			if (PacketIndex < PacketData.ExpectedPackets)
//			{
//				PacketData.Packets[PacketIndex] = Payload;
//			}
//
//			bool bAllReceived = true;
//			for (const TArray<uint8>& Packet : PacketData.Packets)
//			{
//				if (Packet.Num() == 0)
//				{
//					bAllReceived = false;
//					break;
//				}
//			}
//
//			if (bAllReceived)
//			{
//				TArray<uint8> ImageData;
//				for (const TArray<uint8>& Packet : PacketData.Packets)
//				{
//					ImageData.Append(Packet);
//				}
//
//				UTexture2D* Texture = FImageUtils::ImportBufferAsTexture2D(ImageData);
//				if (Texture)
//				{
//					OnTextureReceived.Broadcast(Texture);
//					UE_LOG(LogTemp, Log, TEXT("Texture zusammengesetzt!"));
//				}
//
//				ImagePacketMap.Remove(ImageID);
//			}
//		}
//	}
//}


