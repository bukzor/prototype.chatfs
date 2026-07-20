from chatfs.paths import INCUBATOR_ROOT, demo_root


class DescribeIncubatorRoot:
    def it_points_at_the_directory_containing_the_chatfs_package(self):
        assert (INCUBATOR_ROOT / "chatfs" / "__init__.py").is_file()


class DescribeDemoRoot:
    def it_nests_under_chatfs_demo_by_provider_name(self):
        assert demo_root("claude") == INCUBATOR_ROOT / "chatfs.demo" / "claude"
        assert demo_root("chatgpt") == INCUBATOR_ROOT / "chatfs.demo" / "chatgpt"
