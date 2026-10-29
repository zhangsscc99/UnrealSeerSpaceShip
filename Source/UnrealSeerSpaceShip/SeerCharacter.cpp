#include "SeerCharacter.h"

#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "Engine/SkeletalMesh.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"
#include "InputAction.h"
#include "InputMappingContext.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
	constexpr float MinPitch = -70.f;
	constexpr float MaxPitch = 20.f;

	// Pixels of finger drag per degree of camera rotation.
	constexpr float TouchDegPerPixel = 0.18f;

	constexpr float GamepadLookRate = 120.f; // degrees per second at full deflection
}

ASeerCharacter::ASeerCharacter()
{
	PrimaryActorTick.bCanEverTick = true;

	GetCapsuleComponent()->InitCapsuleSize(34.f, 88.f);

	UCharacterMovementComponent* Move = GetCharacterMovement();
	Move->MaxWalkSpeed = 520.f;
	Move->BrakingDecelerationWalking = 2400.f;
	Move->bOrientRotationToMovement = true;
	Move->RotationRate = FRotator(0.f, 640.f, 0.f);

	// Jumping: one hop from the ground, a second kick in the air.
	Move->JumpZVelocity = 620.f;
	Move->AirControl = 0.6f;
	Move->GravityScale = 1.6f;
	JumpMaxCount = 2;

	bUseControllerRotationPitch = false;
	bUseControllerRotationYaw = false;
	bUseControllerRotationRoll = false;

	static ConstructorHelpers::FObjectFinder<USkeletalMesh> SeerMesh(
		TEXT("/Game/SeerLab/Characters/SK_Seer.SK_Seer"));
	if (SeerMesh.Succeeded())
	{
		GetMesh()->SetSkeletalMesh(SeerMesh.Object);
		GetMesh()->SetRelativeLocation(FVector(0.f, 0.f, -88.f));
		GetMesh()->SetRelativeRotation(FRotator(0.f, -90.f, 0.f));
		GetMesh()->SetRelativeScale3D(FVector(0.01739f));
	}

	// Third-person chase camera: a spring arm keeps the camera behind the character,
	// lags slightly while moving, and pulls in when a wall blocks the view.
	CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
	CameraBoom->SetupAttachment(RootComponent);
	CameraBoom->SetRelativeLocation(FVector(0.f, 0.f, 70.f));
	CameraBoom->bUsePawnControlRotation = true;
	CameraBoom->bInheritPitch = true;
	CameraBoom->bInheritYaw = true;
	CameraBoom->bInheritRoll = false;
	CameraBoom->bEnableCameraLag = true;
	CameraBoom->CameraLagSpeed = 12.f;
	CameraBoom->bDoCollisionTest = true;

	FollowCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("FollowCamera"));
	FollowCamera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);
	FollowCamera->bUsePawnControlRotation = false;
	FollowCamera->FieldOfView = 80.f;

	static ConstructorHelpers::FObjectFinder<UInputAction> MoveAsset(
		TEXT("/Game/Input/IA_Move.IA_Move"));
	if (MoveAsset.Succeeded())
	{
		MoveAction = MoveAsset.Object;
	}

	static ConstructorHelpers::FObjectFinder<UInputMappingContext> ContextA(TEXT("/Game/Input/IMC_A.IMC_A"));
	static ConstructorHelpers::FObjectFinder<UInputMappingContext> ContextD(TEXT("/Game/Input/IMC_D.IMC_D"));
	static ConstructorHelpers::FObjectFinder<UInputMappingContext> ContextW(TEXT("/Game/Input/IMC_W.IMC_W"));
	static ConstructorHelpers::FObjectFinder<UInputMappingContext> ContextS(TEXT("/Game/Input/IMC_S.IMC_S"));
	for (const auto& Finder : { &ContextA, &ContextD, &ContextW, &ContextS })
	{
		if (Finder->Succeeded())
		{
			MappingContexts.Add(Finder->Object);
		}
	}
}

void ASeerCharacter::BeginPlay()
{
	Super::BeginPlay();

	if (APlayerController* PC = Cast<APlayerController>(GetController()))
	{
		if (UEnhancedInputLocalPlayerSubsystem* Subsystem =
			ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(PC->GetLocalPlayer()))
		{
			for (UInputMappingContext* Context : MappingContexts)
			{
				if (Context)
				{
					Subsystem->AddMappingContext(Context, 0);
				}
			}
		}
	}

	ApplyCameraPreset(0);
}

void ASeerCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);

	PlayerInputComponent->BindAxis(TEXT("MoveForward"), this, &ASeerCharacter::MoveForward);
	PlayerInputComponent->BindAxis(TEXT("MoveRight"), this, &ASeerCharacter::MoveRight);
	PlayerInputComponent->BindAxis(TEXT("Turn"), this, &ASeerCharacter::Turn);
	PlayerInputComponent->BindAxis(TEXT("LookUp"), this, &ASeerCharacter::LookUp);
	PlayerInputComponent->BindAxis(TEXT("TurnRate"), this, &ASeerCharacter::TurnRate);
	PlayerInputComponent->BindAxis(TEXT("LookUpRate"), this, &ASeerCharacter::LookUpRate);

	PlayerInputComponent->BindAction(TEXT("Jump"), IE_Pressed, this, &ACharacter::Jump);
	PlayerInputComponent->BindAction(TEXT("Jump"), IE_Released, this, &ACharacter::StopJumping);
	PlayerInputComponent->BindAction(TEXT("CycleCamera"), IE_Pressed, this, &ASeerCharacter::CycleCamera);

	PlayerInputComponent->BindTouch(IE_Pressed, this, &ASeerCharacter::TouchStarted);
	PlayerInputComponent->BindTouch(IE_Repeat, this, &ASeerCharacter::TouchMoved);
	PlayerInputComponent->BindTouch(IE_Released, this, &ASeerCharacter::TouchEnded);
}

void ASeerCharacter::Move(const FInputActionValue& Value)
{
	const FVector2D Axis = Value.Get<FVector2D>();
	MoveForward(Axis.Y);
	MoveRight(Axis.X);
}

void ASeerCharacter::MoveForward(float Value)
{
	if (Controller && FMath::Abs(Value) > KINDA_SMALL_NUMBER)
	{
		const FRotator Yaw(0.f, Controller->GetControlRotation().Yaw, 0.f);
		AddMovementInput(Yaw.Vector(), Value);
	}
}

void ASeerCharacter::MoveRight(float Value)
{
	if (Controller && FMath::Abs(Value) > KINDA_SMALL_NUMBER)
	{
		const FRotator Yaw(0.f, Controller->GetControlRotation().Yaw, 0.f);
		AddMovementInput(FRotationMatrix(Yaw).GetUnitAxis(EAxis::Y), Value);
	}
}

void ASeerCharacter::Turn(float Value)
{
	AddControllerYawInput(Value);
}

void ASeerCharacter::LookUp(float Value)
{
	ApplyLookDelta(0.f, Value);
}

void ASeerCharacter::TurnRate(float Value)
{
	AddControllerYawInput(Value * GamepadLookRate * GetWorld()->GetDeltaSeconds());
}

void ASeerCharacter::LookUpRate(float Value)
{
	ApplyLookDelta(0.f, Value * GamepadLookRate * GetWorld()->GetDeltaSeconds());
}

void ASeerCharacter::CycleCamera()
{
	ApplyCameraPreset((CameraPreset + 1) % 2);
}

void ASeerCharacter::ApplyCameraPreset(int32 Index)
{
	CameraPreset = FMath::Clamp(Index, 0, 1);
	CameraBoom->TargetArmLength = (CameraPreset == 0) ? 450.f : 900.f;
	if (APlayerController* PC = Cast<APlayerController>(GetController()))
	{
		FRotator Rot = PC->GetControlRotation();
		Rot.Pitch = (CameraPreset == 0) ? -14.f : -28.f;
		PC->SetControlRotation(Rot);
	}
}

void ASeerCharacter::ApplyLookDelta(float DeltaYaw, float DeltaPitch)
{
	if (APlayerController* PC = Cast<APlayerController>(GetController()))
	{
		FRotator Rot = PC->GetControlRotation();
		Rot.Yaw += DeltaYaw;
		Rot.Pitch = FMath::ClampAngle(Rot.Pitch + DeltaPitch, MinPitch, MaxPitch);
		PC->SetControlRotation(Rot);
	}
}

void ASeerCharacter::TouchStarted(ETouchIndex::Type FingerIndex, FVector Location)
{
	APlayerController* PC = Cast<APlayerController>(GetController());
	// bUseMouseForTouch makes the desktop mouse emit touches too; the mouse axes
	// already drive the camera there, so only real fingers may claim look.
	if (!PC || FingerIndex == ETouchIndex::CursorPointerIndex || LookFinger != ETouchIndex::MAX_TOUCHES)
	{
		return;
	}

	int32 ViewX = 0, ViewY = 0;
	PC->GetViewportSize(ViewX, ViewY);
	if (Location.X > ViewX * 0.5f)
	{
		LookFinger = FingerIndex;
		LastTouchLocation = FVector2D(Location.X, Location.Y);
	}
}

void ASeerCharacter::TouchMoved(ETouchIndex::Type FingerIndex, FVector Location)
{
	if (FingerIndex != LookFinger)
	{
		return;
	}

	const FVector2D Current(Location.X, Location.Y);
	const FVector2D Delta = Current - LastTouchLocation;
	LastTouchLocation = Current;
	ApplyLookDelta(Delta.X * TouchDegPerPixel, Delta.Y * TouchDegPerPixel);
}

void ASeerCharacter::TouchEnded(ETouchIndex::Type FingerIndex, FVector Location)
{
	if (FingerIndex == LookFinger)
	{
		LookFinger = ETouchIndex::MAX_TOUCHES;
	}
}
