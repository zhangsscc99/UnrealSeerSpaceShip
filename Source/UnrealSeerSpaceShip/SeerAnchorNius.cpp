#include "SeerAnchorNius.h"

#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/PackageName.h"
#include "SeerCommsPanel.h"
#include "UObject/ConstructorHelpers.h"

ASeerAnchorNius::ASeerAnchorNius()
{
	PrimaryActorTick.bCanEverTick = true;

	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);

	Body = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Body"));
	Body->SetupAttachment(Root);
	Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Body->SetMobility(EComponentMobility::Movable);
	Body->SetRelativeScale3D(FVector(2.f, 2.f, 2.f));
	Body->SetCastShadow(true);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> MeshFinder(
		TEXT("/Game/SeerLab/Characters/SM_AnchorNius/StaticMeshes/SM_AnchorNius"));
	if (MeshFinder.Succeeded())
	{
		Body->SetStaticMesh(MeshFinder.Object);
	}

	static ConstructorHelpers::FObjectFinder<UTexture2D> PortraitFinder(
		TEXT("/Game/SeerLab/UI/Textures/T_AnchorNius_Portrait.T_AnchorNius_Portrait"));
	if (PortraitFinder.Succeeded())
	{
		PortraitTexture = PortraitFinder.Object;
	}

	// Three-point lighting. The robot's front is local +Y (it turns to face the
	// player), so the key sits in front of the face instead of straight above it.
	KeyLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("KeyLight"));
	KeyLight->SetupAttachment(Root);
	KeyLight->SetRelativeLocation(FVector(0.f, 135.f, 175.f));
	KeyLight->SetIntensity(36000.f);
	KeyLight->SetAttenuationRadius(1700.f);
	KeyLight->SetLightColor(FLinearColor(1.0f, 0.98f, 0.95f), false);
	KeyLight->SetCastShadows(false);
	KeyLight->SetMobility(EComponentMobility::Movable);

	// Cool rim from behind separates the silhouette from the dark bulkhead.
	RimLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("RimLight"));
	RimLight->SetupAttachment(Root);
	RimLight->SetRelativeLocation(FVector(0.f, -150.f, 240.f));
	RimLight->SetIntensity(15000.f);
	RimLight->SetAttenuationRadius(1200.f);
	RimLight->SetLightColor(FLinearColor(0.45f, 0.88f, 1.0f), false);
	RimLight->SetCastShadows(false);
	RimLight->SetMobility(EComponentMobility::Movable);

	// Warm low fill so the red/white collar and arms keep their material colour.
	FillLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("FillLight"));
	FillLight->SetupAttachment(Root);
	FillLight->SetRelativeLocation(FVector(0.f, 120.f, 25.f));
	FillLight->SetIntensity(10000.f);
	FillLight->SetAttenuationRadius(1000.f);
	FillLight->SetLightColor(FLinearColor(1.0f, 0.88f, 0.76f), false);
	FillLight->SetCastShadows(false);
	FillLight->SetMobility(EComponentMobility::Movable);

	SpeakerName = FText::FromString(TEXT("主播纽斯"));
	SpeakerTag = FText::FromString(TEXT("NEUS-07 · 主播 / BROADCASTER"));
	DialogueText = FText::FromString(TEXT(
		"信号正常，音量正常！小赛尔，你来得正是时候。\n"
		"本主播在这扇门前等了好久——就等一位愿意出发的观众。\n"
		"下一站，克罗斯星：大自然的星球，精灵的快乐天堂。要出发吗？"));
	DestinationName = FText::FromString(TEXT("克罗斯星"));
	DestinationMeta = FText::FromString(TEXT("DEST-01 · 帕诺星系 · 类地行星 · 安全评级 B · 航程 4.2 光年"));
	CtaLabel = FText::FromString(TEXT("前往克罗斯星"));
	UnavailableStatus = FText::FromString(TEXT("克罗斯星航线已锁定 · 跃迁通道正在建设中"));
}

void ASeerAnchorNius::BeginPlay()
{
	Super::BeginPlay();
	IdleYaw = GetActorRotation().Yaw;
	CurrentYaw = IdleYaw;
	HoverTime = 0.f;
}

void ASeerAnchorNius::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (bPanelOpen && Panel.IsValid() && GEngine && GEngine->GameViewport)
	{
		GEngine->GameViewport->RemoveViewportWidgetContent(Panel.ToSharedRef());
	}
	bPanelOpen = false;
	Panel.Reset();
	RestorePlayerInput();

	Super::EndPlay(EndPlayReason);
}

void ASeerAnchorNius::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	HoverTime += DeltaSeconds;

	// Bob and a gentle servo sway; the actor's yaw is reserved for turning to
	// whichever part of the corridor the player is standing in.
	const float Bob = FMath::Sin(HoverTime * HoverSpeed) * HoverAmplitude + HoverAmplitude;
	if (Body)
	{
		Body->SetRelativeLocation(FVector(0.f, 0.f, Bob));
		Body->SetRelativeRotation(FRotator(
			FMath::Sin(HoverTime * 0.70f) * 1.2f,
			FMath::Sin(HoverTime * 0.50f) * 2.5f,
			0.f));
	}

	APawn* PlayerPawn = UGameplayStatics::GetPlayerPawn(this, 0);
	float Distance = TNumericLimits<float>::Max();
	if (PlayerPawn)
	{
		Distance = FVector::Dist(GetActorLocation(), PlayerPawn->GetActorLocation());

		float TargetYaw = IdleYaw;
		if (Distance < 2200.f)
		{
			const FVector ToPlayer = (PlayerPawn->GetActorLocation() - GetActorLocation()).GetSafeNormal2D();
			if (!ToPlayer.IsNearlyZero())
			{
				// The robot's modelled front is local +Y, so this maps +Y onto the player direction.
				TargetYaw = FMath::RadiansToDegrees(FMath::Atan2(-ToPlayer.X, ToPlayer.Y));
			}
		}
		const float DeltaYaw = FMath::FindDeltaAngleDegrees(CurrentYaw, TargetYaw);
		CurrentYaw += DeltaYaw * FMath::Clamp(DeltaSeconds * 3.2f, 0.f, 1.f);
		SetActorRotation(FRotator(0.f, CurrentYaw, 0.f));
	}

	if (!bPanelOpen && !bCooldown && Distance <= TriggerRadius)
	{
		OpenPanel();
	}
	else if (bPanelOpen && Distance > ReleaseRadius && Panel.IsValid())
	{
		Panel->BeginClose();
	}

	if (bCooldown && Distance > ReleaseRadius)
	{
		bCooldown = false;
	}
}

void ASeerAnchorNius::OpenPanel()
{
	if (bPanelOpen)
	{
		return;
	}

	if (!Panel.IsValid())
	{
		Panel = SNew(SSeerCommsPanel)
			.SpeakerName(SpeakerName)
			.SpeakerTag(SpeakerTag)
			.DialogueText(DialogueText)
			.DestinationName(DestinationName)
			.DestinationMeta(DestinationMeta)
			.CtaLabel(CtaLabel)
			.UnavailableStatus(UnavailableStatus)
			.PortraitTexture(PortraitTexture)
			.OnTravelConfirmed(FSimpleDelegate::CreateUObject(this, &ASeerAnchorNius::HandleTravelConfirmed))
			.OnClosed(FSimpleDelegate::CreateUObject(this, &ASeerAnchorNius::HandlePanelClosed));
	}

	if (GEngine && GEngine->GameViewport)
	{
		GEngine->GameViewport->AddViewportWidgetContent(Panel.ToSharedRef(), 10);
	}

	bPanelOpen = true;
	bCooldown = false;
	Panel->PlayIntro();

	if (APlayerController* PC = UGameplayStatics::GetPlayerController(this, 0))
	{
		CachedPC = PC;
		PC->SetIgnoreMoveInput(true);
		PC->SetIgnoreLookInput(true);
		PC->SetVirtualJoystickVisibility(false);
		PC->bShowMouseCursor = true;

		FInputModeGameAndUI InputMode;
		InputMode.SetWidgetToFocus(Panel);
		InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
		InputMode.SetHideCursorDuringCapture(false);
		PC->SetInputMode(InputMode);
	}
}

void ASeerAnchorNius::HandleTravelConfirmed()
{
	if (bAllowTravel)
	{
		const FString LevelName = TravelLevelName.ToString();
		const FString LongPackageName = LevelName.StartsWith(TEXT("/"))
			? LevelName
			: FString::Printf(TEXT("/Game/%s"), *LevelName);

		if (FPackageName::DoesPackageExist(LongPackageName))
		{
			UGameplayStatics::OpenLevel(this, FName(*LevelName));
			return;
		}
	}

	if (Panel.IsValid())
	{
		Panel->ShowStatus(UnavailableStatus);
	}
}

void ASeerAnchorNius::HandlePanelClosed()
{
	if (bPanelOpen && Panel.IsValid() && GEngine && GEngine->GameViewport)
	{
		GEngine->GameViewport->RemoveViewportWidgetContent(Panel.ToSharedRef());
	}

	bPanelOpen = false;
	bCooldown = true;
	RestorePlayerInput();
}

void ASeerAnchorNius::RestorePlayerInput()
{
	APlayerController* PC = CachedPC.Get();
	if (!PC)
	{
		PC = UGameplayStatics::GetPlayerController(this, 0);
	}
	if (PC)
	{
		PC->SetIgnoreMoveInput(false);
		PC->SetIgnoreLookInput(false);
		PC->SetVirtualJoystickVisibility(true);
		PC->bShowMouseCursor = false;
		PC->SetInputMode(FInputModeGameOnly());
	}
	CachedPC.Reset();
}
