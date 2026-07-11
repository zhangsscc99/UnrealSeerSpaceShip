using UnrealBuildTool;

public class UnrealSeerSpaceShip : ModuleRules
{
	public UnrealSeerSpaceShip(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core",
			"CoreUObject",
			"Engine",
			"InputCore",
		});
	}
}
