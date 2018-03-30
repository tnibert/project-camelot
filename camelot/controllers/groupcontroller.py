from ..models import FriendGroup
from .utilities import *
from .genericcontroller import genericcontroller
from .friendcontroller import are_friends

class groupcontroller(genericcontroller):
    """
    Default groups should include something like all_friends, public, private
    """

    def create(self, name):
        """
        create a new friend group
        :param name: name of the group
        :return: reference to the newly created group
        """
        # redundant
        try:
            # check if the name already exists for the current user
            try:
                FriendGroup.objects.get(owner=self.uprofile, name=name)
            # if not, it's a go
            except FriendGroup.DoesNotExist:
                # may want to check length of name here
                newgroup = FriendGroup(name=name, owner=self.uprofile)
                newgroup.save()
                return newgroup
            raise AlreadyExistsException("Group needs unique name")
        except:
            raise

    def add_member(self, groupid, profile):
        """
        Add a friend to a group
        :param groupid: id of group to add to
        :param profile: user profile to add to group
        :return: boolean, true for success
        """
        # assert that the users are in fact friends, or at least pending
        # although who knows, maybe you do want to give someone who isn't your friend certain view access
        try:
            assert (are_friends(profile, self.uprofile, confirmed=True) or are_friends(profile, self.uprofile, confirmed=False))
        except Exception as e:
            # log
            return False

        # check permission
        try:
            # get the group, but only if the owner is the current user
            group = FriendGroup.objects.get(owner=self.uprofile, id=groupid)
        except FriendGroup.DoesNotExist:
            # insert log message here, maybe raise permission exception
            return False

        # check if the profile already exists in the group
        if is_in_group(group, profile):
            # log
            return False

        group.members.add(profile)
        group.save()
        return True


    def delete_group(self):
        pass

    def delete_member(self):
        pass

    def return_groups(self, profile=None):
        """
        Returns a list of the groups for a given user
        :param profile: profile of a user to see groups owned by
        :return: queryset of groups
        """
        if profile is None:
            profile = self.uprofile
        if profile is None:
            return None

        groups = FriendGroup.objects.filter(owner=profile)

        return groups

def is_in_group(group, profile):
    """
    Wrapper to check if profile is in group
    :param group: group to test membership in
    :param profile: profile to test membership of
    :return: boolean, True is profile is in group, False if not
    """
    return group.members.all().filter(id=profile.id).exists()

def return_group_from_id(id):
    # todo: unit test
    """
    Wrapper to return the group based on the id
    :param id: id of group
    :return: group object
    """
    return FriendGroup.objects.get(id=id)