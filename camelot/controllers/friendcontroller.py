from .genericcontroller import genericcontroller
from ..models import Friendship, Profile, FriendGroup
from .utilities import AlreadyExistsException
from django.db.models import Q

class friendcontroller(genericcontroller):

    def add(self, profile):
        """
        add a friend, at the end of this method the friendship will still need to be confirmed
        :param profile: profile of user to add
        :return: boolean, true on success, false on failure
        """
        # in this method we will only create a friendship that is not confirmed
        try:
            # check if a friendship already exists
            try:
                Friendship.objects.get(requester=self.uprofile, requestee=profile)
            except Friendship.DoesNotExist:
                # check reverse case
                try:
                    Friendship.objects.get(requester=profile, requestee=self.uprofile)
                # ok, we can make friendship, yay!
                except Friendship.DoesNotExist:
                    newfriendship = Friendship(requester=self.uprofile, requestee=profile, confirmed=False)
                    newfriendship.save()
                    return newfriendship
            raise AlreadyExistsException("Group needs unique name")
        except:
            raise

    def confirm(self, profile):
        # in this method we will confirm the friendship and add the profile to the profile's friends
        # and add created time
        """
        Confirm a friend request
        :param profile: the requester of the friendship to confirm
        :return: boolean, True on success, False on failure
        """
        # check if a valid friend request exists
        try:
            relation = Friendship.objects.get(requester=profile, requestee=self.uprofile, confirmed=False)
        except Friendship.DoesNotExist:
            return False

        # check that the friendship is unconfirmed and that the current user is the valid requestee
        if not relation.confirmed and relation.requestee == self.uprofile:
            relation.confirmed = True
            relation.save()
            # need to add friend to profile?
            return True
        else:
            return False

    def delete(self):
        pass

    def return_friend_list(self, profile):
        """

        :param profile: profile who's friends to return
        :return: queryset containing all friend profiles
        """
        # way broken
        # this doesn't make sense, figure it out
        return profile.friends.all().filter(Q(requestee__confirmed=True) | Q(requester__confirmed=True))

    def return_pending_requests(self):
        """

        :return: queryset containing all unconfirmed friendships for the current user
        """
        return Friendship.objects.all().filter(requestee=self.uprofile, confirmed=False)