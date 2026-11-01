#pragma once

#include "CoreMinimal.h"
#include "Engine/Texture2D.h"
#include "Fonts/SlateFontInfo.h"
#include "Input/Reply.h"
#include "InputCoreTypes.h"
#include "Styling/SlateBrush.h"
#include "Styling/SlateTypes.h"
#include "UObject/StrongObjectPtr.h"
#include "Widgets/SCompoundWidget.h"

class FSeerDialogInputProcessor;
class SBox;
class SButton;
class SImage;
class STextBlock;

/**
 * Full-screen holographic comms console shown when the player reaches
 * 主播纽斯 (Anchor Nius). Built entirely in Slate/C++ so the panel needs no
 * UMG asset authoring; every glass panel, ring, glow and icon is generated
 * procedurally at construction time. The only bitmap is the broadcaster
 * portrait.
 *
 * Visual language: dark teal glass, cyan hairlines, one amber action, live
 * broadcast telemetry (ON AIR dot, waveform, signal bars, scan sweep).
 */
class SSeerCommsPanel : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SSeerCommsPanel) {}
		SLATE_ARGUMENT(FText, SpeakerName)
		SLATE_ARGUMENT(FText, SpeakerTag)
		SLATE_ARGUMENT(FText, DialogueText)
		SLATE_ARGUMENT(FText, DestinationName)
		SLATE_ARGUMENT(FText, DestinationMeta)
		SLATE_ARGUMENT(FText, CtaLabel)
		SLATE_ARGUMENT(FText, UnavailableStatus)
		SLATE_ARGUMENT(TWeakObjectPtr<UTexture2D>, PortraitTexture)
		SLATE_EVENT(FSimpleDelegate, OnTravelConfirmed)
		SLATE_EVENT(FSimpleDelegate, OnClosed)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);
	virtual ~SSeerCommsPanel();

	virtual void Tick(const FGeometry& AllottedGeometry, const double InCurrentTime, const float InDeltaTime) override;
	virtual bool SupportsKeyboardFocus() const override { return true; }

	/** Restart the entrance, typewriter and idle state. Called every time the panel is shown. */
	void PlayIntro();

	/** Fade out and notify the owner through OnClosed once the exit animation is done. */
	void BeginClose();

	/** Show a one-line result under the route card (e.g. route not built yet) and auto-close. */
	void ShowStatus(const FText& InStatus);

	/** Keyboard routing from the input pre-processor (Enter/Esc work regardless of focus). */
	bool HandleDialogKey(const FKey& Key);

private:
	FReply HandleRouteClicked();
	FReply HandleCloseClicked();
	void CompleteTyping();
	void ConfirmRoute();
	void RegisterInput();
	void UnregisterInput();
	void RefreshVisibleText();
	void UpdateAnimations(float DeltaTime, const FVector2D& ViewSize);

	UTexture2D* LoadPortrait() const;

	// --- arguments / resolved content -------------------------------------
	FText SpeakerName;
	FText SpeakerTag;
	FText DialogueText;
	FText DestinationName;
	FText DestinationMeta;
	FText CtaLabel;
	FText UnavailableStatus;
	TWeakObjectPtr<UTexture2D> PortraitTexture;
	FSimpleDelegate OnTravelConfirmed;
	FSimpleDelegate OnClosed;

	// --- generated textures (GC-rooted) -----------------------------------
	TStrongObjectPtr<UTexture2D> PanelTexture;
	TStrongObjectPtr<UTexture2D> ScrimTexture;
	TStrongObjectPtr<UTexture2D> CardTexture;
	TStrongObjectPtr<UTexture2D> CardHoverTexture;
	TStrongObjectPtr<UTexture2D> GlowTexture;
	TStrongObjectPtr<UTexture2D> RingTexture;
	TStrongObjectPtr<UTexture2D> RingDashTexture;
	TStrongObjectPtr<UTexture2D> ScanTexture;
	TStrongObjectPtr<UTexture2D> SweepTexture;
	TStrongObjectPtr<UTexture2D> TextScrimTexture;
	TStrongObjectPtr<UTexture2D> PillTexture;
	TStrongObjectPtr<UTexture2D> PlanetTexture;
	TStrongObjectPtr<UTexture2D> PortraitTextureRef;

	// --- brushes / styles / fonts (must outlive the widget tree) ----------
	FSlateBrush PanelBrush;
	FSlateBrush ScrimBrush;
	FSlateBrush CardBrush;
	FSlateBrush CardHoverBrush;
	FSlateBrush GlowBrush;
	FSlateBrush RingBrush;
	FSlateBrush RingDashBrush;
	FSlateBrush ScanBrush;
	FSlateBrush SweepBrush;
	FSlateBrush TextScrimBrush;
	FSlateBrush PillBrush;
	FSlateBrush PlanetBrush;
	FSlateBrush PortraitBrush;
	FSlateBrush TransparentBrush;
	FButtonStyle RouteStyle;
	FButtonStyle CloseStyle;

	FSlateFontInfo NameFont;
	FSlateFontInfo TitleFont;
	FSlateFontInfo BodyFont;
	FSlateFontInfo CtaFont;
	FSlateFontInfo SmallFont;
	FSlateFontInfo MetaFont;
	FSlateFontInfo TinyFont;

	// --- widgets -----------------------------------------------------------
	TSharedPtr<SBox> ContentRoot;
	TSharedPtr<SImage> ScrimWidget;
	TSharedPtr<STextBlock> BodyText;
	TSharedPtr<STextBlock> StatusText;
	TSharedPtr<SBox> StatusBox;
	TSharedPtr<SButton> RouteButton;
	TSharedPtr<SButton> CloseButton;
	TSharedPtr<SImage> RouteGlow;
	TSharedPtr<STextBlock> CtaText;
	TSharedPtr<STextBlock> ChevronText;
	TSharedPtr<SImage> LiveDot;
	TSharedPtr<SImage> PortraitGlow;
	TSharedPtr<SImage> PortraitImage;
	TSharedPtr<SImage> RingImage;
	TSharedPtr<SImage> RingDashImage;
	TSharedPtr<SImage> SweepImage;
	TSharedPtr<SImage> ProgressBar;
	TArray<TSharedPtr<SImage>> SignalBars;
	TArray<TSharedPtr<SImage>> WaveBars;
	TArray<TSharedPtr<SImage>> IdleRules;
	TArray<TSharedPtr<STextBlock>> IdleTexts;

	// --- animation state ---------------------------------------------------
	float AnimTime = 0.f;
	float CloseStart = 0.f;
	float ConfirmStart = 0.f;
	float StatusStart = 0.f;
	float HoverAlpha = 0.f;
	float TypingAccumulator = 0.f;
	int32 VisibleChars = 0;
	bool bTyping = true;
	bool bConfirming = false;
	bool bConfirmFired = false;
	bool bStatusShown = false;
	bool bClosing = false;

	TSharedPtr<FSeerDialogInputProcessor> InputProcessor;
};
